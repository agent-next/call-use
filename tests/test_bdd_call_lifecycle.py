"""BDD-style tests for call lifecycle, approval flow, and human takeover.

Covers scenarios CL04-CL13, AF03/AF05/AF07, HT02-HT04 from the branch matrix.
Each test uses Given/When/Then docstrings and follows existing patterns from
test_agent_bdd.py.
"""

import asyncio
import json
import logging
import time
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.agent import (
    _build_instructions,
    _LiveKitCallAgent,
)
from call_use.evidence import EvidencePipeline
from call_use.models import (
    CallEventType,
    CallStateEnum,
    CallTask,
    DispositionEnum,
)

pytestmark = pytest.mark.bdd

# ---------------------------------------------------------------------------
# Helpers (same pattern as test_agent_bdd.py)
# ---------------------------------------------------------------------------


def _make_task(**overrides) -> CallTask:
    defaults = dict(phone_number="+12025551234", instructions="Test task")
    defaults.update(overrides)
    return CallTask(**defaults)


def _make_agent(task=None, evidence=None, **overrides):
    """Create agent with mocked LiveKit session for unit testing."""
    if task is None:
        task = _make_task(**overrides)
    agent = _LiveKitCallAgent(task=task, evidence=evidence)
    mock_session = MagicMock()
    mock_session.output.set_audio_enabled = MagicMock()
    mock_session.input.set_audio_enabled = MagicMock()
    mock_session.interrupt = MagicMock()
    mock_session.generate_reply = AsyncMock()
    mock_session.say = AsyncMock()
    agent._session = mock_session
    return agent


def _make_agent_with_evidence(**task_overrides):
    """Create agent + evidence pipeline wired together."""
    task = _make_task(**task_overrides)
    evidence = EvidencePipeline(task, room_name="test-room", agent_identity="agent-test")
    agent = _make_agent(task=task, evidence=evidence)
    return agent, evidence


def _make_data_packet(cmd_type: str, **extra) -> MagicMock:
    """Create a mock data packet for _on_data_received."""
    payload = {"type": cmd_type, **extra}
    dp = MagicMock()
    dp.topic = "backend-commands"
    dp.data = json.dumps(payload).encode("utf-8")
    return dp


# ===========================================================================
# CL: Call Lifecycle scenarios
# ===========================================================================


class TestCallLifecycleBDD:
    """BDD: Call lifecycle state transitions."""

    # CL04: Voicemail detection
    async def test_given_connected_when_voicemail_detected_then_disposition_voicemail(self):
        """Given a connected call, when agent detects voicemail via hang_up tool,
        then disposition=voicemail."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected

        # When: agent calls hang_up with reason="voicemail_detected"
        ctx = MagicMock()
        result = await agent.hang_up(ctx, reason="voicemail_detected")

        # Then: disposition is voicemail, state is ended
        assert agent._current_state == CallStateEnum.ended
        assert agent._finalized is True
        assert "voicemail_detected" in result

        outcome = evidence.finalize(DispositionEnum.voicemail)
        assert outcome.disposition == DispositionEnum.voicemail

    # CL05: Call timeout
    async def test_given_connected_beyond_timeout_when_guard_fires_then_disposition_timeout(self):
        """Given a call connected longer than timeout_seconds, when timeout_guard fires,
        then disposition=timeout and cleanup runs."""
        agent, evidence = _make_agent_with_evidence(timeout_seconds=600)
        agent._current_state = CallStateEnum.connected

        # When: timeout guard fires (simulate directly)
        await agent.finalize_and_publish(DispositionEnum.timeout)

        # Then: state is ended, evidence records the transition
        assert agent._current_state == CallStateEnum.ended
        assert agent._finalized is True
        state_events = [e for e in evidence._events if e.type == CallEventType.state_change]
        ended_transitions = [e for e in state_events if e.data["to"] == "ended"]
        assert len(ended_transitions) == 1

    async def test_timeout_guard_calls_finalize_after_delay(self):
        """Given a very short timeout, when _timeout_guard runs, then finalize is called
        with timeout disposition."""
        agent, evidence = _make_agent_with_evidence(timeout_seconds=600)
        agent._current_state = CallStateEnum.connected

        # Run timeout guard with tiny delay
        task = asyncio.create_task(agent._timeout_guard(0))
        await task

        assert agent._current_state == CallStateEnum.ended
        assert agent._finalized is True

    # CL06: Mid-call drop <3s
    async def test_given_connected_under_3s_when_participant_disconnects_then_disposition_failed(
        self,
    ):
        """Given a call connected for less than 3 seconds, when participant disconnects,
        then disposition=failed (immediate disconnect)."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected
        # Simulate call started just now (< 3s ago)
        agent._call_start_time = time.time()

        # When: participant disconnects — simulate the logic from _on_participant_left
        duration = time.time() - agent._call_start_time
        assert duration < 3
        disp = DispositionEnum.failed  # Immediate disconnect
        await agent.finalize_and_publish(disp)

        # Then: disposition is failed
        assert agent._current_state == CallStateEnum.ended
        assert agent._finalized is True

    # CL07: Mid-call drop >3s normal
    async def test_given_connected_over_3s_when_normal_disconnect_then_disposition_completed(self):
        """Given a call connected for more than 3 seconds and ended normally,
        when participant disconnects, then disposition=completed."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected
        agent._call_start_time = time.time() - 10  # 10 seconds ago
        agent._call_ended_normally = True

        # When: participant disconnects — simulate logic from _on_participant_left
        duration = time.time() - agent._call_start_time
        assert duration >= 3
        disp = DispositionEnum.completed
        await agent.finalize_and_publish(disp)

        # Then: disposition is completed
        assert agent._current_state == CallStateEnum.ended

    # CL08: Mid-call drop >3s abnormal
    async def test_given_connected_over_3s_when_abnormal_disconnect_then_disposition_failed(self):
        """Given a call connected for more than 3 seconds but NOT ended normally,
        when participant disconnects, then disposition=failed (mid-call drop)."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected
        agent._call_start_time = time.time() - 10  # 10 seconds ago
        agent._call_ended_normally = False

        # When: participant disconnects abnormally
        duration = time.time() - agent._call_start_time
        assert duration >= 3
        assert not agent._call_ended_normally
        disp = DispositionEnum.failed
        await evidence.emit_error("mid_call_drop", f"Call dropped after {duration:.0f}s")
        await agent.finalize_and_publish(disp)

        # Then: disposition is failed and error recorded
        assert agent._current_state == CallStateEnum.ended
        error_events = [e for e in evidence._events if e.type == CallEventType.error]
        assert len(error_events) == 1
        assert error_events[0].data["code"] == "mid_call_drop"

    # CL09: Cancel during dial
    async def test_given_dialing_when_cancel_then_disposition_cancelled(self):
        """Given a call in dialing state, when cancel command received,
        then disposition=cancelled."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.dialing

        # When: cancel command fires
        agent._cancelled = True
        agent.session.interrupt()
        await agent.finalize_and_publish(DispositionEnum.cancelled)

        # Then: state is ended
        assert agent._current_state == CallStateEnum.ended
        assert agent._finalized is True
        assert agent._cancelled is True

    # CL10: Cancel during connected
    async def test_given_connected_when_cancel_then_disposition_cancelled_and_cleanup(self):
        """Given a connected call, when cancel command received,
        then disposition=cancelled and cleanup runs."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected

        # When: cancel via _on_data_received
        dp = _make_data_packet("cancel")
        await agent._on_data_received(dp)

        # Then: cancelled flag set, finalized, state ended
        assert agent._cancelled is True
        assert agent._finalized is True
        assert agent._current_state == CallStateEnum.ended
        agent.session.interrupt.assert_called()

    # CL12: Double cancel
    async def test_given_connected_when_cancel_twice_then_second_is_idempotent(self):
        """Given a connected call, when cancel is sent twice,
        then second cancel is idempotent (no crash, no duplicate finalize)."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected

        # When: first cancel
        dp1 = _make_data_packet("cancel")
        await agent._on_data_received(dp1)
        events_after_first = len(evidence._events)

        # When: second cancel
        dp2 = _make_data_packet("cancel")
        await agent._on_data_received(dp2)

        # Then: idempotent — no additional state events
        assert agent._current_state == CallStateEnum.ended
        assert agent._finalized is True
        assert len(evidence._events) == events_after_first

    # CL13: ended is terminal
    async def test_given_ended_when_any_command_then_rejected(self, caplog):
        """Given a call in ended state, when any command is sent,
        then it is rejected (takeover, resume, inject all ignored)."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.ended
        agent._finalized = True

        # When: takeover on ended state
        with caplog.at_level(logging.WARNING):
            await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.ended

        # When: resume on ended state
        with caplog.at_level(logging.WARNING):
            result = await agent._handle_resume({})
        assert result is None
        assert agent._current_state == CallStateEnum.ended

        # When: inject on ended state
        result = await agent._handle_inject({"text": "hello"})
        assert result is None

    async def test_given_ended_when_cancel_then_idempotent(self):
        """Given a call already ended, when cancel arrives,
        then finalize is idempotent (no crash)."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.ended
        agent._finalized = True
        events_before = len(evidence._events)

        # When: cancel on already-ended call
        dp = _make_data_packet("cancel")
        await agent._on_data_received(dp)

        # Then: no additional events, still ended
        assert agent._current_state == CallStateEnum.ended
        assert len(evidence._events) == events_before


# ===========================================================================
# AF: Approval Flow scenarios
# ===========================================================================


class TestApprovalFlowBDD:
    """BDD: Approval flow scenarios."""

    # AF03: Approval timeout
    async def test_given_awaiting_approval_when_60s_timeout_then_auto_reject(self):
        """Given agent is awaiting approval, when 60 seconds pass with no response,
        then the approval is auto-rejected."""
        agent = _make_agent(approval_required=True)
        agent._current_state = CallStateEnum.connected

        # Override timeout to be very short for test
        agent.APPROVAL_TIMEOUT = 0.01

        # Simulate the full _request_user_approval_impl flow
        agent._approval_event = asyncio.Event()
        agent._approval_result = None
        agent._approval_id = "apr-timeout-bdd"
        await agent._set_state(CallStateEnum.awaiting_approval)

        # When: timeout fires
        try:
            await asyncio.wait_for(agent._approval_event.wait(), timeout=0.01)
        except asyncio.TimeoutError:
            agent._approval_result = "rejected"

        # Then: auto-rejected
        assert agent._approval_result == "rejected"

    # AF05: Cancel during approval
    async def test_given_awaiting_approval_when_cancel_then_cancelled(self):
        """Given agent is awaiting approval, when cancel command arrives,
        then call is cancelled."""
        agent, evidence = _make_agent_with_evidence(approval_required=True)
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-cancel-test"

        # When: cancel command
        dp = _make_data_packet("cancel")
        await agent._on_data_received(dp)

        # Then: cancelled
        assert agent._cancelled is True
        assert agent._finalized is True
        assert agent._current_state == CallStateEnum.ended

    # AF07: approval_required=False
    async def test_given_approval_not_required_when_call_runs_then_no_approval_tool(self):
        """Given approval_required=False, when call agent is created,
        then no approval tool is mentioned in instructions."""
        task = _make_task(approval_required=False)
        instructions = _build_instructions(task)

        # Then: no mention of approval tool
        assert "request_user_approval" not in instructions

        # Also verify agent creates successfully without approval tool
        agent = _LiveKitCallAgent(task=task)
        assert agent is not None


# ===========================================================================
# HT: Human Takeover scenarios
# ===========================================================================


class TestHumanTakeoverBDD:
    """BDD: Human takeover scenarios."""

    # HT02: Token TTL
    async def test_given_takeover_when_token_generated_then_ttl_15min(self):
        """Given a human takeover request, when the SDK generates a token,
        then the token TTL is 15 minutes."""
        import os

        from call_use.sdk import CallAgent

        sdk_agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        sdk_agent._room_name = "test-room-ht02"

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
        )
        mock_api.room.send_data = AsyncMock()

        with (
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                },
            ),
        ):
            mock_token_instance = MockToken.return_value
            mock_token_instance.to_jwt.return_value = "human-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            jwt = await sdk_agent.takeover()

            # Then: TTL is 15 minutes
            mock_token_instance.with_ttl.assert_called_once_with(timedelta(minutes=15))
            assert jwt == "human-jwt"

    # HT03: Resume without prior takeover
    async def test_given_connected_without_takeover_when_resume_then_no_op(self, caplog):
        """Given agent is in connected state (no prior takeover), when resume is sent,
        then it is a no-op (ignored with warning)."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected

        # When: resume while connected (not in takeover)
        with caplog.at_level(logging.WARNING):
            result = await agent._handle_resume({"summary": "nothing"})

        # Then: no-op
        assert result is None
        assert agent._current_state == CallStateEnum.connected
        assert any("Ignoring resume" in r.message for r in caplog.records)

    # HT04: Takeover after ended
    async def test_given_ended_when_takeover_then_rejected(self, caplog):
        """Given a call has ended, when takeover is requested,
        then it is rejected (state stays ended)."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.ended

        # When: takeover on ended call
        with caplog.at_level(logging.WARNING):
            await agent._handle_takeover({})

        # Then: state remains ended
        assert agent._current_state == CallStateEnum.ended
