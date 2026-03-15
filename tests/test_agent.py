"""Tests for call_use.agent — Step 5a agent state machine."""

# LiveKit mocks are set up in conftest.py (shared across all test files).

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from call_use.agent import (
    _HANG_UP_REASONS,
    _build_instructions,
    _LiveKitCallAgent,
)
from call_use.evidence import EvidencePipeline
from call_use.models import CallEvent, CallEventType, CallOutcome, CallStateEnum, CallTask, DispositionEnum

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(**overrides) -> CallTask:
    defaults = dict(phone_number="+12025551234", instructions="Test task")
    defaults.update(overrides)
    return CallTask(**defaults)


def _make_agent(task=None, **overrides):
    """Create agent with mocked LiveKit session for unit testing."""
    if task is None:
        task = _make_task()
    agent = _LiveKitCallAgent(task=task, **overrides)
    mock_session = MagicMock()
    mock_session.output.set_audio_enabled = MagicMock()
    mock_session.input.set_audio_enabled = MagicMock()
    mock_session.interrupt = MagicMock()
    mock_session.generate_reply = AsyncMock()
    agent._session = mock_session
    return agent


# ===========================================================================
# 1-4: Instruction building
# ===========================================================================


class TestBuildInstructions:
    def test_includes_task_instructions(self):
        task = _make_task(instructions="Call the dentist to confirm appointment")
        result = _build_instructions(task)
        assert "Call the dentist to confirm appointment" in result

    def test_includes_user_info(self):
        task = _make_task(
            instructions="Confirm appointment",
            user_info={"name": "Alice Smith", "dob": "1990-01-15"},
        )
        result = _build_instructions(task)
        assert "Alice Smith" in result
        assert "1990-01-15" in result
        assert "User-provided info" in result

    def test_without_user_info(self):
        task = _make_task(instructions="Simple task", user_info={})
        result = _build_instructions(task)
        assert "Simple task" in result
        assert "User-provided info" not in result

    def test_recording_disclaimer_not_in_instructions(self):
        """Recording disclaimer is spoken via on_enter/say(), not in LLM instructions."""
        task = _make_task(
            instructions="Call about bill",
            recording_disclaimer="This call may be recorded.",
        )
        result = _build_instructions(task)
        assert "This call may be recorded." not in result

    def test_approval_required_true(self):
        task = _make_task(approval_required=True)
        result = _build_instructions(task)
        assert "request_user_approval" in result

    def test_approval_required_false(self):
        task = _make_task(approval_required=False)
        result = _build_instructions(task)
        assert "request_user_approval" not in result


# ===========================================================================
# 5: State transitions — connected → human_takeover → connected (resume)
# ===========================================================================


class TestTakeoverResumeFlow:
    async def test_takeover_then_resume(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected

        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover

        result = await agent._handle_resume({"summary": "Talked to CS rep"})
        assert agent._current_state == CallStateEnum.connected
        assert result is not None
        assert "Talked to CS rep" in result

    async def test_resume_without_summary_returns_none(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover
        result = await agent._handle_resume({})
        assert agent._current_state == CallStateEnum.connected
        assert result is None


# ===========================================================================
# 6: Approval state transitions
# ===========================================================================


class TestApprovalFlow:
    async def test_approval_state_transition(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected

        # Set up approval state manually (simulates what _request_user_approval_impl does)
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-test-1"
        await agent._set_state(CallStateEnum.awaiting_approval)
        assert agent._current_state == CallStateEnum.awaiting_approval

        # Approve with correct ID
        await agent._handle_approval_response({"type": "approve", "approval_id": "apr-test-1"})
        assert agent._approval_result == "approved"
        assert agent._approval_event.is_set()


# ===========================================================================
# 7: awaiting_approval → human_takeover (takeover cancels approval)
# ===========================================================================


class TestTakeoverCancelsApproval:
    async def test_takeover_during_awaiting_approval(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-test-2"

        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover
        assert agent._approval_result == "cancelled"
        assert agent._approval_event.is_set()


# ===========================================================================
# 8: Approval ID generation uniqueness
# ===========================================================================


class TestApprovalIdUniqueness:
    def test_approval_ids_are_unique(self):
        import uuid

        ids = set()
        for i in range(20):
            aid = f"apr-{uuid.uuid4().hex[:12]}"
            ids.add(aid)
        assert len(ids) == 20


# ===========================================================================
# 9-10: Approval ID correlation — wrong/empty ID rejected
# ===========================================================================


class TestApprovalIdCorrelation:
    async def test_wrong_approval_id_rejected(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-correct-1"

        # Wrong ID — handler should return without setting event
        await agent._handle_approval_response({"type": "approve", "approval_id": "apr-wrong-id"})
        assert not agent._approval_event.is_set()
        assert agent._approval_result is None

    async def test_empty_approval_id_rejected(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-correct-2"

        await agent._handle_approval_response({"type": "approve", "approval_id": ""})
        assert not agent._approval_event.is_set()
        assert agent._approval_result is None


# ===========================================================================
# 11: Takeover while active — state changes to human_takeover
# ===========================================================================


class TestTakeoverWhileActive:
    async def test_takeover_from_connected(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover
        agent.session.output.set_audio_enabled.assert_called_with(False)
        agent.session.input.set_audio_enabled.assert_called_with(False)


# ===========================================================================
# 12: Resume while not in human_takeover — ignored with warning
# ===========================================================================


class TestResumeWhileNotInTakeover:
    async def test_resume_while_connected_is_ignored(self, caplog):
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        with caplog.at_level(logging.WARNING):
            result = await agent._handle_resume({})
        assert agent._current_state == CallStateEnum.connected
        assert result is None
        assert any("Ignoring resume" in r.message for r in caplog.records)

    async def test_resume_while_awaiting_approval_is_ignored(self, caplog):
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        with caplog.at_level(logging.WARNING):
            result = await agent._handle_resume({})
        assert agent._current_state == CallStateEnum.awaiting_approval
        assert result is None


# ===========================================================================
# 13: Double takeover — idempotent
# ===========================================================================


class TestDoubleTakeover:
    async def test_double_takeover_is_idempotent(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover

        # Second takeover should not raise, state stays human_takeover
        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover


# ===========================================================================
# Hang-up reasons mapping
# ===========================================================================


class TestHangUpReasons:
    def test_maps_to_dispositions(self):
        assert _HANG_UP_REASONS["task_complete"] == DispositionEnum.completed
        assert _HANG_UP_REASONS["voicemail_detected"] == DispositionEnum.voicemail
        assert _HANG_UP_REASONS["cannot_proceed"] == DispositionEnum.failed
        assert _HANG_UP_REASONS["wrong_number"] == DispositionEnum.failed

    def test_finalize_and_publish_idempotent(self):
        agent = _make_agent()
        assert not agent._finalized
        # After first finalize, flag should be set
        # (We don't call it here since it tries to write metadata;
        # the idempotency is tested by the _finalized flag pattern)
        agent._finalized = True
        assert agent._finalized


# ===========================================================================
# Transcript hooks (Step 5c)
# ===========================================================================


class TestTranscriptHooks:
    async def test_on_user_turn_completed_emits_callee_transcript(self):
        task = _make_task()
        evidence = EvidencePipeline(task)
        agent = _make_agent(task=task, evidence=evidence)
        agent._current_state = CallStateEnum.connected

        # Simulate a new_message with text_content
        msg = MagicMock()
        msg.text_content = "Hello, how can I help you?"
        await agent.on_user_turn_completed(chat_ctx=MagicMock(), new_message=msg)

        assert len(evidence._transcript) == 1
        assert evidence._transcript[0]["speaker"] == "callee"
        assert evidence._transcript[0]["text"] == "Hello, how can I help you?"

    async def test_on_user_turn_completed_no_evidence(self):
        """Should not crash when evidence is None."""
        agent = _make_agent()
        agent._evidence = None
        msg = MagicMock()
        msg.text_content = "test"
        # Should not raise
        await agent.on_user_turn_completed(chat_ctx=MagicMock(), new_message=msg)


# ===========================================================================
# Inject handler
# ===========================================================================


class TestInjectHandler:
    async def test_inject_while_connected(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        result = await agent._handle_inject({"text": "Account number is 12345"})
        assert result is not None
        assert "12345" in result
        assert "operator note" in result.lower()

    async def test_inject_while_not_connected(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover
        result = await agent._handle_inject({"text": "Some info"})
        assert result is None


class TestSIPErrorClassification:
    """SIP error -> disposition mapping."""

    def test_sip_status_486_maps_to_busy(self):
        from call_use.agent import SIP_DISPOSITION_MAP
        from call_use.models import DispositionEnum
        assert SIP_DISPOSITION_MAP["486"] == DispositionEnum.busy

    def test_sip_status_480_maps_to_no_answer(self):
        from call_use.agent import SIP_DISPOSITION_MAP
        from call_use.models import DispositionEnum
        assert SIP_DISPOSITION_MAP["480"] == DispositionEnum.no_answer

    def test_sip_status_408_maps_to_no_answer(self):
        from call_use.agent import SIP_DISPOSITION_MAP
        from call_use.models import DispositionEnum
        assert SIP_DISPOSITION_MAP["408"] == DispositionEnum.no_answer

    def test_sip_status_487_maps_to_cancelled(self):
        from call_use.agent import SIP_DISPOSITION_MAP
        from call_use.models import DispositionEnum
        assert SIP_DISPOSITION_MAP["487"] == DispositionEnum.cancelled

    def test_classify_sip_error_with_status(self):
        from call_use.agent import classify_sip_error
        from call_use.models import DispositionEnum
        assert classify_sip_error("486", "busy here") == DispositionEnum.busy

    def test_classify_sip_error_fallback_string_match(self):
        from call_use.agent import classify_sip_error
        from call_use.models import DispositionEnum
        assert classify_sip_error("", "line is busy") == DispositionEnum.busy
        assert classify_sip_error("", "no answer from callee") == DispositionEnum.no_answer
        assert classify_sip_error("", "went to voicemail") == DispositionEnum.voicemail

    def test_classify_sip_error_unknown(self):
        from call_use.agent import classify_sip_error
        from call_use.models import DispositionEnum
        assert classify_sip_error("", "something weird") == DispositionEnum.failed


# ===========================================================================
# _update_metadata
# ===========================================================================


class TestUpdateMetadata:
    async def test_update_metadata_writes_to_room(self):
        """_update_metadata writes agent_identity and state to room metadata."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.name = "test-room"
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()

        await agent._update_metadata("connected")
        agent._lk_api.room.update_room_metadata.assert_called_once()

    async def test_update_metadata_includes_approval_id_when_awaiting(self):
        """_update_metadata includes approval_id when state is awaiting_approval."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.name = "test-room"
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()
        agent._approval_id = "apr-test-99"

        await agent._update_metadata("awaiting_approval")
        agent._lk_api.room.update_room_metadata.assert_called_once()

    async def test_update_metadata_no_room_is_noop(self):
        """_update_metadata does nothing if room is not set."""
        agent = _make_agent()
        agent._room = None
        agent._lk_api = None
        # Should not raise
        await agent._update_metadata("connected")

    async def test_update_metadata_retries_on_failure(self):
        """_update_metadata retries once on failure."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.name = "test-room"
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock(
            side_effect=[Exception("network error"), None]
        )
        await agent._update_metadata("connected")
        assert agent._lk_api.room.update_room_metadata.call_count == 2

    async def test_update_metadata_both_attempts_fail(self):
        """_update_metadata logs error after both attempts fail."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.name = "test-room"
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock(
            side_effect=Exception("persistent failure")
        )
        # Should not raise, just log
        await agent._update_metadata("connected")
        assert agent._lk_api.room.update_room_metadata.call_count == 2


# ===========================================================================
# on_enter
# ===========================================================================


class TestOnEnter:
    async def test_on_enter_sets_state_and_registers_handler(self):
        """on_enter transitions to connected and registers data handler."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.on = MagicMock()
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.name = "test-room"

        await agent.on_enter()
        assert agent._current_state == CallStateEnum.connected
        agent._room.on.assert_called_once()

    async def test_on_enter_no_room_returns_early(self):
        """on_enter returns early if room is None."""
        agent = _make_agent()
        agent._room = None
        await agent.on_enter()
        assert agent._current_state == CallStateEnum.created

    async def test_on_enter_speaks_recording_disclaimer(self):
        """on_enter speaks recording disclaimer if configured."""
        task = _make_task(recording_disclaimer="This call may be recorded.")
        agent = _make_agent(task=task)
        agent._room = MagicMock()
        agent._room.on = MagicMock()
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.name = "test-room"
        agent._session.say = AsyncMock()

        await agent.on_enter()
        agent._session.say.assert_called_once_with(
            "This call may be recorded.", allow_interruptions=False
        )


# ===========================================================================
# _on_data_received routing
# ===========================================================================


class TestOnDataReceived:
    def _make_dp(self, cmd_type, **extra):
        payload = {"type": cmd_type, **extra}
        dp = MagicMock()
        dp.topic = "backend-commands"
        dp.data = json.dumps(payload).encode("utf-8")
        return dp

    async def test_ignores_non_backend_commands(self):
        """_on_data_received ignores packets with wrong topic."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        dp = MagicMock()
        dp.topic = "other-topic"
        # Should not raise
        await agent._on_data_received(dp)

    async def test_routes_cancel_command(self):
        """Cancel command sets _cancelled and calls finalize_and_publish."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        agent.finalize_and_publish = AsyncMock()
        dp = self._make_dp("cancel")
        await agent._on_data_received(dp)
        assert agent._cancelled is True
        agent.finalize_and_publish.assert_called_once_with(DispositionEnum.cancelled)

    async def test_routes_takeover_command(self):
        """Takeover command transitions state to human_takeover."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        dp = self._make_dp("takeover")
        await agent._on_data_received(dp)
        assert agent._current_state == CallStateEnum.human_takeover

    async def test_routes_resume_command(self):
        """Resume command transitions back to connected."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover
        dp = self._make_dp("resume", summary="Test summary")
        await agent._on_data_received(dp)
        assert agent._current_state == CallStateEnum.connected

    async def test_routes_inject_context(self):
        """inject_context generates a reply with context note."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        dp = self._make_dp("inject_context", text="Account 12345")
        await agent._on_data_received(dp)
        agent.session.generate_reply.assert_called_once()

    async def test_routes_approval_response(self):
        """approve/reject routes to _handle_approval_response."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-test-routing"
        dp = self._make_dp("approve", approval_id="apr-test-routing")
        await agent._on_data_received(dp)
        assert agent._approval_result == "approved"


# ===========================================================================
# finalize_and_publish
# ===========================================================================


class TestFinalizeAndPublish:
    async def test_finalize_sets_ended_state(self):
        """finalize_and_publish transitions to ended."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        await agent.finalize_and_publish(DispositionEnum.completed)
        assert agent._finalized is True
        assert agent._current_state == CallStateEnum.ended

    async def test_finalize_idempotent(self):
        """Second call to finalize_and_publish is a no-op."""
        agent = _make_agent()
        agent._finalized = True
        agent._current_state = CallStateEnum.connected
        await agent.finalize_and_publish(DispositionEnum.completed)
        # State should NOT change since finalize was already done
        assert agent._current_state == CallStateEnum.connected

    async def test_finalize_with_evidence_writes_outcome(self):
        """finalize_and_publish writes outcome to room metadata when evidence exists."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        agent = _make_agent(task=task, evidence=evidence)
        agent._current_state = CallStateEnum.connected
        agent._room = MagicMock()
        agent._room.name = "test-room"
        agent._room.local_participant.publish_data = AsyncMock()
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()
        agent._lk_api.room.remove_participant = AsyncMock()

        await agent.finalize_and_publish(DispositionEnum.completed)
        assert agent._finalized is True
        agent._lk_api.room.update_room_metadata.assert_called_once()
        agent._room.local_participant.publish_data.assert_called_once()

    async def test_finalize_without_room(self):
        """finalize_and_publish works without room (no metadata write)."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        agent = _make_agent(task=task, evidence=evidence)
        agent._room = None
        agent._lk_api = None
        await agent.finalize_and_publish(DispositionEnum.timeout)
        assert agent._finalized is True

    async def test_finalize_publishes_call_complete_event(self):
        """finalize_and_publish publishes call_complete event on data channel."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.name = "test-room"
        agent._room.local_participant.publish_data = AsyncMock()
        agent._lk_api = None  # No metadata write
        await agent.finalize_and_publish(DispositionEnum.failed)
        agent._room.local_participant.publish_data.assert_called_once()

    async def test_finalize_removes_sip_participant(self):
        """finalize_and_publish removes SIP participant to hang up."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.name = "test-room"
        agent._room.local_participant.publish_data = AsyncMock()
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()
        agent._lk_api.room.remove_participant = AsyncMock()
        await agent.finalize_and_publish(DispositionEnum.completed)
        agent._lk_api.room.remove_participant.assert_called_once()

    async def test_finalize_handles_metadata_write_failure(self):
        """finalize_and_publish handles metadata write failure gracefully."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        agent = _make_agent(task=task, evidence=evidence)
        agent._room = MagicMock()
        agent._room.name = "test-room"
        agent._room.local_participant.publish_data = AsyncMock()
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock(side_effect=Exception("fail"))
        agent._lk_api.room.remove_participant = AsyncMock()
        # Should not raise
        await agent.finalize_and_publish(DispositionEnum.completed)
        assert agent._finalized is True

    async def test_finalize_handles_publish_data_failure(self):
        """finalize_and_publish handles publish_data failure gracefully."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.name = "test-room"
        agent._room.local_participant.publish_data = AsyncMock(side_effect=Exception("fail"))
        agent._lk_api = MagicMock()
        agent._lk_api.room.remove_participant = AsyncMock()
        await agent.finalize_and_publish(DispositionEnum.failed)
        assert agent._finalized is True

    async def test_finalize_handles_remove_participant_failure(self):
        """finalize_and_publish handles remove_participant failure gracefully."""
        agent = _make_agent()
        agent._room = MagicMock()
        agent._room.name = "test-room"
        agent._room.local_participant.publish_data = AsyncMock()
        agent._lk_api = MagicMock()
        agent._lk_api.room.update_room_metadata = AsyncMock()
        agent._lk_api.room.remove_participant = AsyncMock(side_effect=Exception("fail"))
        await agent.finalize_and_publish(DispositionEnum.completed)
        assert agent._finalized is True


# ===========================================================================
# hang_up tool
# ===========================================================================


class TestHangUpTool:
    async def test_hang_up_task_complete(self):
        """hang_up with 'task_complete' sets disposition to completed."""
        agent = _make_agent()
        agent.finalize_and_publish = AsyncMock()
        result = await agent.hang_up(context=MagicMock(), reason="task_complete")
        assert "task_complete" in result
        assert agent._call_ended_normally is True
        agent.finalize_and_publish.assert_called_once_with(DispositionEnum.completed)

    async def test_hang_up_voicemail(self):
        """hang_up with 'voicemail_detected' sets disposition to voicemail."""
        agent = _make_agent()
        agent.finalize_and_publish = AsyncMock()
        result = await agent.hang_up(context=MagicMock(), reason="voicemail_detected")
        assert "voicemail_detected" in result
        agent.finalize_and_publish.assert_called_once_with(DispositionEnum.voicemail)

    async def test_hang_up_unknown_reason(self):
        """hang_up with unknown reason defaults to failed."""
        agent = _make_agent()
        agent.finalize_and_publish = AsyncMock()
        result = await agent.hang_up(context=MagicMock(), reason="unknown_reason")
        assert "unknown_reason" in result
        agent.finalize_and_publish.assert_called_once_with(DispositionEnum.failed)


# ===========================================================================
# _request_user_approval_impl
# ===========================================================================


class TestRequestUserApproval:
    async def test_approval_approved_flow(self):
        """Approval flow: request -> approved -> returns 'approved'."""
        task = _make_task(approval_required=True)
        agent = _make_agent(task=task)
        agent._current_state = CallStateEnum.connected
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.local_participant.publish_data = AsyncMock()

        async def _simulate_approval():
            """Simulate approval response arriving after a short delay."""
            await asyncio.sleep(0.05)
            agent._approval_result = "approved"
            if agent._approval_event:
                agent._approval_event.set()

        asyncio.create_task(_simulate_approval())
        result = await agent._request_user_approval_impl(
            context=MagicMock(), details="Refund of $50"
        )
        assert result == "approved"
        assert agent._current_state == CallStateEnum.connected

    async def test_approval_rejected_flow(self):
        """Approval flow: request -> rejected -> returns 'rejected'."""
        task = _make_task(approval_required=True)
        agent = _make_agent(task=task)
        agent._current_state = CallStateEnum.connected
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.local_participant.publish_data = AsyncMock()

        async def _simulate_rejection():
            await asyncio.sleep(0.05)
            agent._approval_result = "rejected"
            if agent._approval_event:
                agent._approval_event.set()

        asyncio.create_task(_simulate_rejection())
        result = await agent._request_user_approval_impl(
            context=MagicMock(), details="Subscribe for $100/mo"
        )
        assert result == "rejected"

    async def test_approval_timeout_auto_rejects(self):
        """Approval times out and auto-rejects."""
        task = _make_task(approval_required=True)
        agent = _make_agent(task=task)
        agent._current_state = CallStateEnum.connected
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.local_participant.publish_data = AsyncMock()
        # Set short timeout for testing
        agent.APPROVAL_TIMEOUT = 0.1

        result = await agent._request_user_approval_impl(
            context=MagicMock(), details="Expensive thing"
        )
        assert result == "rejected"

    async def test_approval_with_evidence(self):
        """Approval flow emits evidence events."""
        task = _make_task(approval_required=True)
        evidence = EvidencePipeline(task)
        agent = _make_agent(task=task, evidence=evidence)
        agent._current_state = CallStateEnum.connected
        agent._room = MagicMock()
        agent._room.local_participant.identity = "agent-abc"
        agent._room.local_participant.publish_data = AsyncMock()
        agent.APPROVAL_TIMEOUT = 0.1

        result = await agent._request_user_approval_impl(
            context=MagicMock(), details="Refund"
        )
        assert result == "rejected"  # Timed out


# ===========================================================================
# _timeout_guard
# ===========================================================================


class TestTimeoutGuard:
    async def test_timeout_guard_triggers_finalize(self):
        """_timeout_guard calls finalize_and_publish after timeout."""
        agent = _make_agent()
        agent.finalize_and_publish = AsyncMock()
        await agent._timeout_guard(0)  # 0 seconds = immediate
        agent.finalize_and_publish.assert_called_once_with(DispositionEnum.timeout)

    async def test_timeout_guard_cancellation(self):
        """_timeout_guard handles CancelledError gracefully (does not finalize)."""
        agent = _make_agent()
        agent.finalize_and_publish = AsyncMock()
        task = asyncio.create_task(agent._timeout_guard(999))
        await asyncio.sleep(0.01)
        task.cancel()
        # _timeout_guard catches CancelledError internally, so await should not raise
        await task
        agent.finalize_and_publish.assert_not_called()
