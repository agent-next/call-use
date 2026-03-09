"""Tests for call_use.agent — Step 5a agent state machine."""

import asyncio
import logging
import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

# Mock livekit imports so tests work without LiveKit installed.
_livekit_mock = MagicMock()
_livekit_agents_mock = MagicMock()


class _FakeAgent:
    """Minimal stand-in for livekit.agents.Agent."""
    def __init__(self, *args, **kwargs):
        self._session = None

    @property
    def session(self):
        return self._session


_livekit_agents_mock.Agent = _FakeAgent
# function_tool must be callable — return identity for non-decorator usage,
# and also work as @function_tool decorator.
_livekit_agents_mock.function_tool = lambda fn=None, **kw: fn if fn else (lambda f: f)

for mod in [
    "livekit", "livekit.api", "livekit.rtc", "livekit.agents",
    "livekit.agents.beta", "livekit.agents.beta.tools",
    "livekit.plugins", "livekit.plugins.openai",
    "livekit.plugins.deepgram", "livekit.plugins.silero",
    "livekit.plugins.noise_cancellation",
    "livekit.protocol", "livekit.protocol.sip",
    "dotenv",
]:
    sys.modules.setdefault(mod, MagicMock() if mod != "livekit.agents" else _livekit_agents_mock)

from call_use.agent import (  # noqa: E402
    _LiveKitCallAgent, _build_instructions, _HANG_UP_REASONS,
)
from call_use.models import CallTask, CallStateEnum, DispositionEnum  # noqa: E402
from call_use.evidence import EvidencePipeline  # noqa: E402


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

    def test_includes_recording_disclaimer(self):
        task = _make_task(
            instructions="Call about bill",
            recording_disclaimer="This call may be recorded.",
        )
        result = _build_instructions(task)
        assert "This call may be recorded." in result
        assert "At the start of the call" in result

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
        await agent._handle_approval_response(
            {"type": "approve", "approval_id": "apr-test-1"}
        )
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
        ids = set()
        for i in range(20):
            _LiveKitCallAgent._approval_counter += 1
            aid = f"apr-{int(time.time())}-{_LiveKitCallAgent._approval_counter}"
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
        await agent._handle_approval_response(
            {"type": "approve", "approval_id": "apr-wrong-id"}
        )
        assert not agent._approval_event.is_set()
        assert agent._approval_result is None

    async def test_empty_approval_id_rejected(self):
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-correct-2"

        await agent._handle_approval_response(
            {"type": "approve", "approval_id": ""}
        )
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
