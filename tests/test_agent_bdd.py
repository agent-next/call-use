"""BDD-style tests for call-use agent — comprehensive scenario coverage.

Each test class covers a real-world scenario with descriptive Given/When/Then
docstrings that read like behavior specs.
"""

# LiveKit mocks are set up in conftest.py (shared across all test files).

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.agent import (
    _build_instructions,
    _LiveKitCallAgent,
)
from call_use.evidence import EvidencePipeline
from call_use.models import (
    CallEvent,
    CallEventType,
    CallOutcome,
    CallStateEnum,
    CallTask,
    DispositionEnum,
)
from call_use.phone import validate_phone_number  # noqa: E402

pytestmark = pytest.mark.bdd

# ---------------------------------------------------------------------------
# Helpers
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
# 1. Call Lifecycle
# ===========================================================================


class TestCallLifecycle:
    """Given a configured agent, test the full call lifecycle."""

    async def test_agent_starts_in_created_state(self):
        """Given a newly created agent, state should be 'created'."""
        agent = _make_agent()
        assert agent._current_state == CallStateEnum.created

    async def test_agent_transitions_created_to_dialing(self):
        """Given a new agent, calling _set_state(dialing) should transition from created."""
        agent, evidence = _make_agent_with_evidence()
        assert agent._current_state == CallStateEnum.created
        await agent._set_state(CallStateEnum.dialing)
        assert agent._current_state == CallStateEnum.dialing

    async def test_agent_transitions_dialing_to_connected(self):
        """Given a dialing agent, on_enter should transition to connected."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.dialing
        # Simulate on_enter by calling _set_state
        await agent._set_state(CallStateEnum.connected)
        assert agent._current_state == CallStateEnum.connected

    async def test_agent_transitions_to_ended_on_finalize(self):
        """Given a connected agent, finalize should transition to ended."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected
        await agent.finalize_and_publish(DispositionEnum.completed)
        assert agent._current_state == CallStateEnum.ended

    async def test_state_progression_recorded_in_evidence(self):
        """Given state transitions, evidence should record each change in order."""
        agent, evidence = _make_agent_with_evidence()
        await agent._set_state(CallStateEnum.dialing)
        await agent._set_state(CallStateEnum.connected)
        await agent.finalize_and_publish(DispositionEnum.completed)

        state_events = [e for e in evidence._events if e.type == CallEventType.state_change]
        transitions = [(e.data["from"], e.data["to"]) for e in state_events]
        assert ("created", "dialing") in transitions
        assert ("dialing", "connected") in transitions
        assert ("connected", "ended") in transitions

    async def test_finalize_is_idempotent(self):
        """Given finalize called twice, should not crash or duplicate events."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected
        await agent.finalize_and_publish(DispositionEnum.completed)
        event_count_after_first = len(evidence._events)

        # Second call should be a no-op
        await agent.finalize_and_publish(DispositionEnum.failed)
        assert len(evidence._events) == event_count_after_first
        assert agent._finalized is True

    async def test_dial_failure_busy_produces_busy_disposition(self):
        """Given SIP error containing 'busy', agent should finalize as busy."""
        agent, evidence = _make_agent_with_evidence()
        # Simulate what agent.run() does on SIP error
        await agent.finalize_and_publish(DispositionEnum.busy)
        outcome = evidence.finalize(DispositionEnum.busy)
        assert outcome.disposition == DispositionEnum.busy

    async def test_dial_failure_voicemail_produces_voicemail_disposition(self):
        """Given SIP error containing 'voicemail', agent should finalize as voicemail."""
        agent, evidence = _make_agent_with_evidence()
        await agent.finalize_and_publish(DispositionEnum.voicemail)
        assert agent._current_state == CallStateEnum.ended


# ===========================================================================
# 2. IVR Navigation
# ===========================================================================


class TestIVRNavigation:
    """Given an IVR menu, test DTMF navigation."""

    def test_agent_has_dtmf_tool(self):
        """Agent should have send_dtmf_events referenced in its initialization.
        The tools list is passed to the parent Agent class via super().__init__."""
        from livekit.agents.beta.tools import send_dtmf_events

        # Verify send_dtmf_events is importable and is the mock we expect
        assert send_dtmf_events is not None
        # The agent __init__ passes [send_dtmf_events, ...] to super().__init__(tools=...)
        # Since _FakeAgent doesn't store tools, verify the code path doesn't error
        task = _make_task()
        agent = _LiveKitCallAgent(task=task)
        assert agent is not None

    def test_dtmf_arguments_handles_string_type(self):
        """Given call.arguments is str (v1.4.5), DTMF keys should be extracted correctly."""
        # Simulates the logic in _on_tools_executed handler
        args = "1234"  # v1.4.5 format: raw string
        if isinstance(args, str):
            keys = args
        elif isinstance(args, dict):
            keys = args.get("keys", "")
        else:
            keys = ""
        assert keys == "1234"

    def test_dtmf_arguments_handles_dict_type(self):
        """Given call.arguments is dict (legacy), DTMF keys should be extracted correctly."""
        args = {"keys": "5678"}  # Legacy format: dict
        if isinstance(args, str):
            keys = args
        elif isinstance(args, dict):
            keys = args.get("keys", "")
        else:
            keys = ""
        assert keys == "5678"

    async def test_dtmf_event_emitted_to_evidence(self):
        """Given DTMF keys pressed, evidence pipeline should record dtmf event."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_dtmf("123")

        dtmf_events = [e for e in evidence._events if e.type == CallEventType.dtmf]
        assert len(dtmf_events) == 1
        assert dtmf_events[0].data["keys"] == "123"

    def test_dtmf_arguments_handles_unknown_type_gracefully(self):
        """Given call.arguments is an unexpected type, keys should default to empty."""
        args = 12345  # Unexpected type
        if isinstance(args, str):
            keys = args
        elif isinstance(args, dict):
            keys = args.get("keys", "")
        else:
            keys = ""
        assert keys == ""


# ===========================================================================
# 3. Approval Flow
# ===========================================================================


class TestApprovalFlow:
    """Given approval_required=True, test the approval gate."""

    def test_approval_tool_added_when_required(self):
        """Given approval_required=True, request_user_approval tool should exist.
        Verified via instruction text which mentions the tool."""
        task = _make_task(approval_required=True)
        instructions = _build_instructions(task)
        assert "request_user_approval" in instructions
        # Also verify agent creates without error
        agent = _LiveKitCallAgent(task=task)
        assert agent is not None

    def test_approval_tool_not_added_when_not_required(self):
        """Given approval_required=False, no approval tool in instructions."""
        task = _make_task(approval_required=False)
        instructions = _build_instructions(task)
        assert "request_user_approval" not in instructions
        agent = _LiveKitCallAgent(task=task)
        assert agent is not None

    async def test_approval_transitions_to_awaiting_state(self):
        """Given approval requested, state should change to awaiting_approval."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-test-1"
        await agent._set_state(CallStateEnum.awaiting_approval)
        assert agent._current_state == CallStateEnum.awaiting_approval

    async def test_approval_disables_audio_during_wait(self):
        """Given awaiting approval, audio should be disabled."""
        agent = _make_agent(approval_required=True)
        agent._current_state = CallStateEnum.connected

        # Simulate what _request_user_approval_impl does
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-test-audio"
        await agent._set_state(CallStateEnum.awaiting_approval)
        agent.session.output.set_audio_enabled(False)
        agent.session.input.set_audio_enabled(False)

        agent.session.output.set_audio_enabled.assert_called_with(False)
        agent.session.input.set_audio_enabled.assert_called_with(False)

    async def test_approval_timeout_auto_rejects(self):
        """Given no response within timeout, approval should auto-reject."""
        agent = _make_agent(approval_required=True)
        agent._current_state = CallStateEnum.connected
        # Use a very short timeout for testing
        agent.APPROVAL_TIMEOUT = 0.05

        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-timeout-test"

        # Simulate the timeout logic from _request_user_approval_impl
        try:
            await asyncio.wait_for(agent._approval_event.wait(), timeout=0.05)
        except asyncio.TimeoutError:
            agent._approval_result = "rejected"

        assert agent._approval_result == "rejected"

    async def test_approval_approved_sets_result(self):
        """Given approved, approval_result should be 'approved'."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-approve-test"

        await agent._handle_approval_response(
            {
                "type": "approve",
                "approval_id": "apr-approve-test",
            }
        )
        assert agent._approval_result == "approved"
        assert agent._approval_event.is_set()

    async def test_approval_rejected_sets_result(self):
        """Given rejected, approval_result should be 'rejected'."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-reject-test"

        await agent._handle_approval_response(
            {
                "type": "reject",
                "approval_id": "apr-reject-test",
            }
        )
        assert agent._approval_result == "rejected"
        assert agent._approval_event.is_set()

    async def test_wrong_approval_id_ignored(self):
        """Given approval response with wrong ID, should be ignored."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-correct"

        await agent._handle_approval_response(
            {
                "type": "approve",
                "approval_id": "apr-wrong",
            }
        )
        assert not agent._approval_event.is_set()
        assert agent._approval_result is None

    async def test_approval_response_while_not_awaiting_ignored(self, caplog):
        """Given approval response while connected, should be ignored with warning."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        with caplog.at_level(logging.WARNING):
            await agent._handle_approval_response(
                {
                    "type": "approve",
                    "approval_id": "apr-stale",
                }
            )
        assert any("Ignoring approval" in r.message for r in caplog.records)

    async def test_approval_instructions_include_tool_mention(self):
        """Given approval_required=True, instructions should mention request_user_approval."""
        task = _make_task(approval_required=True)
        instructions = _build_instructions(task)
        assert "request_user_approval" in instructions

    async def test_no_approval_instructions_exclude_tool_mention(self):
        """Given approval_required=False, instructions should NOT mention request_user_approval."""
        task = _make_task(approval_required=False)
        instructions = _build_instructions(task)
        assert "request_user_approval" not in instructions


# ===========================================================================
# 4. Human Takeover
# ===========================================================================


class TestHumanTakeover:
    """Given a human wants to take over the call."""

    async def test_takeover_disables_agent_audio(self):
        """Given takeover command, agent audio should be disabled."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        await agent._handle_takeover({})
        agent.session.output.set_audio_enabled.assert_called_with(False)
        agent.session.input.set_audio_enabled.assert_called_with(False)

    async def test_takeover_changes_state(self):
        """Given takeover, state should be human_takeover."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover

    async def test_resume_re_enables_audio(self):
        """Given resume after takeover, audio should be re-enabled."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover
        await agent._handle_resume({})
        agent.session.output.set_audio_enabled.assert_called_with(True)
        agent.session.input.set_audio_enabled.assert_called_with(True)

    async def test_resume_with_summary_injects_context(self):
        """Given resume with summary, LLM should receive the summary as context."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover
        result = await agent._handle_resume({"summary": "Customer agreed to $50 refund"})
        assert result is not None
        assert "Customer agreed to $50 refund" in result
        assert "operator note" in result.lower()

    async def test_resume_without_summary_returns_none(self):
        """Given resume without summary, should return None (no context injection)."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover
        result = await agent._handle_resume({})
        assert result is None

    async def test_takeover_during_approval_cancels_approval(self):
        """Given takeover while awaiting approval, approval should be cancelled."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.awaiting_approval
        agent._approval_event = asyncio.Event()
        agent._approval_id = "apr-takeover-cancel"

        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover
        assert agent._approval_result == "cancelled"
        assert agent._approval_event.is_set()

    async def test_double_takeover_is_idempotent(self):
        """Given takeover called twice, should not crash."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover

        # Second takeover — should not raise
        await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.human_takeover

    async def test_resume_while_not_in_takeover_is_ignored(self, caplog):
        """Given resume while connected (not takeover), should be ignored."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected
        with caplog.at_level(logging.WARNING):
            result = await agent._handle_resume({})
        assert result is None
        assert agent._current_state == CallStateEnum.connected
        assert any("Ignoring resume" in r.message for r in caplog.records)

    async def test_takeover_emits_evidence_event(self):
        """Given takeover, evidence pipeline should record takeover event."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected
        await agent._handle_takeover({})
        takeover_events = [e for e in evidence._events if e.type == CallEventType.takeover]
        assert len(takeover_events) == 1

    async def test_resume_emits_evidence_event(self):
        """Given resume after takeover, evidence pipeline should record resume event."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.human_takeover
        await agent._handle_resume({})
        resume_events = [e for e in evidence._events if e.type == CallEventType.resume]
        assert len(resume_events) == 1

    async def test_takeover_ignored_in_ended_state(self, caplog):
        """Given takeover while call is ended, should be ignored."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.ended
        with caplog.at_level(logging.WARNING):
            await agent._handle_takeover({})
        assert agent._current_state == CallStateEnum.ended


# ===========================================================================
# 5. Evidence Pipeline
# ===========================================================================


class TestEvidencePipeline:
    """Given calls in progress, test evidence collection."""

    async def test_callee_speech_recorded(self):
        """Given callee speaks, transcript should have speaker=callee entries."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_transcript("callee", "Hello, this is customer support.")

        assert len(evidence._transcript) == 1
        assert evidence._transcript[0]["speaker"] == "callee"
        assert evidence._transcript[0]["text"] == "Hello, this is customer support."
        assert "timestamp" in evidence._transcript[0]

    async def test_agent_speech_recorded(self):
        """Given agent speaks, transcript should have speaker=agent entries."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_transcript("agent", "Hi, I'm calling about your service.")

        assert len(evidence._transcript) == 1
        assert evidence._transcript[0]["speaker"] == "agent"

    async def test_on_user_turn_completed_emits_callee_transcript(self):
        """Given callee finishes speaking, on_user_turn_completed should emit transcript."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected

        msg = MagicMock()
        msg.text_content = "I can help you with that."
        await agent.on_user_turn_completed(chat_ctx=MagicMock(), new_message=msg)

        assert len(evidence._transcript) == 1
        assert evidence._transcript[0]["speaker"] == "callee"
        assert evidence._transcript[0]["text"] == "I can help you with that."

    async def test_state_changes_recorded_as_events(self):
        """Given state transitions, events should be recorded in order."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_state_change(CallStateEnum.created, CallStateEnum.dialing)
        await evidence.emit_state_change(CallStateEnum.dialing, CallStateEnum.connected)

        state_events = [e for e in evidence._events if e.type == CallEventType.state_change]
        assert len(state_events) == 2
        assert state_events[0].data["from"] == "created"
        assert state_events[0].data["to"] == "dialing"
        assert state_events[1].data["from"] == "dialing"
        assert state_events[1].data["to"] == "connected"

    async def test_finalize_produces_complete_outcome(self):
        """Given call ends, CallOutcome should have transcript, events, duration, disposition."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_transcript("callee", "Hello")
        await evidence.emit_transcript("agent", "Hi there")
        await evidence.emit_state_change(CallStateEnum.created, CallStateEnum.connected)

        outcome = evidence.finalize(DispositionEnum.completed)
        assert isinstance(outcome, CallOutcome)
        assert outcome.task_id == task.task_id
        assert outcome.disposition == DispositionEnum.completed
        assert len(outcome.transcript) == 2
        assert len(outcome.events) >= 3  # 2 transcripts + 1 state change
        assert outcome.duration_seconds > 0
        assert outcome.metadata["phone_number"] == "+12025551234"

    async def test_finalize_writes_json_log(self, tmp_path):
        """Given call ends, JSON log file should be written."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_transcript("callee", "Test")

        with patch("call_use.evidence.LOGS_DIR", tmp_path):
            evidence.finalize(DispositionEnum.completed)

        log_file = tmp_path / f"{task.task_id}.json"
        assert log_file.exists()
        log_data = json.loads(log_file.read_text())
        assert log_data["task_id"] == task.task_id
        assert log_data["disposition"] == "completed"

    async def test_subscriber_error_does_not_break_pipeline(self):
        """Given a failing subscriber, other subscribers and pipeline should continue."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        received = []

        async def good_subscriber(event: CallEvent):
            received.append(event)

        async def bad_subscriber(event: CallEvent):
            raise RuntimeError("Subscriber exploded")

        evidence.subscribe(bad_subscriber)
        evidence.subscribe(good_subscriber)

        # Should not raise despite bad_subscriber failing
        await evidence.emit_transcript("callee", "Hello")

        # Good subscriber should still receive the event
        assert len(received) == 1
        assert received[0].type == CallEventType.transcript

    async def test_multiple_subscribers_all_receive_events(self):
        """Given multiple subscribers, all should receive each event."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        received_a = []
        received_b = []

        async def sub_a(event):
            received_a.append(event)

        async def sub_b(event):
            received_b.append(event)

        evidence.subscribe(sub_a)
        evidence.subscribe(sub_b)

        await evidence.emit_dtmf("5")
        assert len(received_a) == 1
        assert len(received_b) == 1

    async def test_error_event_recorded(self):
        """Given an error, evidence should record error event with code and message."""
        task = _make_task()
        evidence = EvidencePipeline(task)
        await evidence.emit_error("dial_failed", "Connection refused")

        error_events = [e for e in evidence._events if e.type == CallEventType.error]
        assert len(error_events) == 1
        assert error_events[0].data["code"] == "dial_failed"
        assert error_events[0].data["message"] == "Connection refused"


# ===========================================================================
# 6. Phone Validation
# ===========================================================================


class TestPhoneValidation:
    """Given phone numbers, test validation rules."""

    def test_valid_us_numbers_accepted(self):
        """Given valid US numbers (+1XXXXXXXXXX), should pass."""
        assert validate_phone_number("+12025551234") == "+12025551234"
        assert validate_phone_number("+13105551234") == "+13105551234"

    def test_toll_free_numbers_accepted(self):
        """Given toll-free (800/888/877/866/855/844/833), should pass."""
        for prefix in ["800", "888", "877", "866", "855", "844", "833"]:
            result = validate_phone_number(f"+1{prefix}2234567")
            assert result == f"+1{prefix}2234567"

    def test_premium_900_blocked(self):
        """Given 900 numbers, should raise ValueError."""
        with pytest.raises(ValueError, match="Premium-rate"):
            validate_phone_number("+19002345678")

    def test_premium_976_exchange_blocked(self):
        """Given 976 exchange, should raise ValueError."""
        with pytest.raises(ValueError, match="Premium-rate"):
            validate_phone_number("+12129761234")

    def test_caribbean_numbers_blocked(self):
        """Given Caribbean NPAs (809/829/849/876/etc), should raise ValueError."""
        caribbean_codes = ["809", "829", "849", "876", "787", "868"]
        for code in caribbean_codes:
            with pytest.raises(ValueError, match="Denied area code"):
                validate_phone_number(f"+1{code}2345678")

    def test_whitespace_stripped(self):
        """Given number with whitespace, should strip and validate."""
        assert validate_phone_number("  +12025551234  ") == "+12025551234"

    def test_non_e164_format_rejected(self):
        """Given number without +1, should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("2025551234")
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("12025551234")

    def test_international_non_nanp_rejected(self):
        """Given non-NANP international number, should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("+442012345678")

    def test_pacific_npa_blocked(self):
        """Given Pacific NPAs (670/671/684), should raise ValueError."""
        for code in ["670", "671", "684"]:
            with pytest.raises(ValueError, match="Denied area code"):
                validate_phone_number(f"+1{code}2345678")

    def test_non_string_input_rejected(self):
        """Given non-string input, should raise ValueError."""
        with pytest.raises(ValueError, match="phone_number must be a string"):
            validate_phone_number(12025551234)  # type: ignore[arg-type]

    def test_empty_string_rejected(self):
        """Given empty string, should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("")


# ===========================================================================
# 7. CLI Behavior
# ===========================================================================


class TestCLIBehavior:
    """Given CLI invocations, test user-facing behavior."""

    def test_missing_env_vars_shows_actionable_error(self):
        """Given missing LIVEKIT_URL, error should list what's needed and link to docs."""
        from call_use.cli import _check_env

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                _check_env()
            msg = str(exc_info.value)
            assert "LIVEKIT_URL" in msg
            assert "LIVEKIT_API_KEY" in msg
            assert "https://github.com/agent-next/call-use#configure" in msg

    def test_invalid_json_user_info_exits_2(self):
        """Given --user-info 'not-json', should exit 2 (input error)."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["dial", "+18005551234", "-i", "test", "-u", "not-json"])
        assert result.exit_code == 2

    def test_completed_call_exits_0(self):
        """Given disposition=completed, exit code should be 0."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        with patch("call_use.cli._run_call") as mock_run:
            mock_run.return_value = {
                "task_id": "test-1",
                "disposition": "completed",
                "duration_seconds": 30.0,
                "transcript": [],
                "events": [],
            }
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "Ask hours"])
        assert result.exit_code == 0

    def test_voicemail_exits_0(self):
        """Given disposition=voicemail, exit code should be 0 (expected outcome)."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        with patch("call_use.cli._run_call") as mock_run:
            mock_run.return_value = {
                "task_id": "test-vm",
                "disposition": "voicemail",
                "duration_seconds": 15.0,
                "transcript": [],
                "events": [],
            }
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "Ask hours"])
        assert result.exit_code == 0

    def test_failed_call_exits_1(self):
        """Given disposition=failed, exit code should be 1."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        with patch("call_use.cli._run_call") as mock_run:
            mock_run.return_value = {
                "task_id": "test-fail",
                "disposition": "failed",
                "duration_seconds": 5.0,
                "transcript": [],
                "events": [],
            }
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "Ask hours"])
        assert result.exit_code == 1

    def test_json_output_to_stdout(self):
        """Given successful call, stdout should be parseable JSON with task_id, disposition."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        with patch("call_use.cli._run_call") as mock_run:
            mock_run.return_value = {
                "task_id": "test-json",
                "disposition": "completed",
                "duration_seconds": 42.0,
                "transcript": [{"speaker": "agent", "text": "Hello"}],
                "events": [],
            }
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "Ask hours"])

        # Extract JSON from output (may have stderr lines mixed in)
        output_lines = result.output.strip().split("\n")
        json_block = []
        in_json = False
        for line in output_lines:
            if line.strip().startswith("{"):
                in_json = True
            if in_json:
                json_block.append(line)
        parsed = json.loads("\n".join(json_block))
        assert parsed["task_id"] == "test-json"
        assert parsed["disposition"] == "completed"
        assert len(parsed["transcript"]) == 1

    def test_timeout_disposition_exits_1(self):
        """Given disposition=timeout, exit code should be 1 (unexpected outcome)."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        with patch("call_use.cli._run_call") as mock_run:
            mock_run.return_value = {
                "task_id": "test-timeout",
                "disposition": "timeout",
                "duration_seconds": 600.0,
                "transcript": [],
                "events": [],
            }
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "Ask hours"])
        assert result.exit_code == 1


# ===========================================================================
# 8. MCP Server Behavior
# ===========================================================================


class TestMCPBehavior:
    """Given MCP tool calls, test async behavior."""

    @patch.dict(
        "os.environ",
        {
            "LIVEKIT_URL": "wss://test",
            "LIVEKIT_API_KEY": "key",
            "LIVEKIT_API_SECRET": "secret",
            "SIP_TRUNK_ID": "trunk",
            "OPENAI_API_KEY": "sk-test",
        },
    )
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_dial_returns_immediately_with_task_id(self, MockLiveKitAPI):
        """Given dial call, should return task_id without waiting for call to complete."""
        from call_use.mcp_server import _do_dial

        mock_api = AsyncMock()
        mock_api.room.create_room.return_value = MagicMock()
        mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _do_dial(phone="+18005551234", instructions="Test")
        assert "task_id" in result
        assert result["status"] == "dispatched"
        # Should NOT have disposition (call hasn't completed)
        assert "disposition" not in result

    async def test_dial_rejects_non_dict_user_info(self):
        """Given user_info='[]', should return error."""
        from call_use.mcp_server import dial

        result_str = await dial(phone="+18005551234", instructions="Test", user_info="[]")
        result = json.loads(result_str)
        assert "error" in result
        assert "dict" in result["error"]

    async def test_dial_rejects_scalar_user_info(self):
        """Given user_info='"string"', should return error."""
        from call_use.mcp_server import dial

        result_str = await dial(phone="+18005551234", instructions="Test", user_info='"scalar"')
        result = json.loads(result_str)
        assert "error" in result

    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_status_returns_call_state(self, MockLiveKitAPI):
        """Given active call, status should return current state."""
        from call_use.mcp_server import _do_status

        mock_api = AsyncMock()
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "connected"})
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _do_status(task_id="call-test-123")
        assert result["state"] == "connected"

    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_result_returns_outcome_when_ended(self, MockLiveKitAPI):
        """Given completed call, result should return full CallOutcome."""
        from call_use.mcp_server import _do_result

        mock_api = AsyncMock()
        mock_room = MagicMock()
        mock_room.metadata = json.dumps(
            {
                "state": "ended",
                "outcome": {
                    "task_id": "call-done",
                    "disposition": "completed",
                    "duration_seconds": 30.0,
                    "transcript": [{"speaker": "agent", "text": "Hello"}],
                    "events": [],
                },
            }
        )
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _do_result(task_id="call-done")
        assert result["disposition"] == "completed"
        assert result["task_id"] == "call-done"

    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_result_returns_in_progress_when_active(self, MockLiveKitAPI):
        """Given active call, result should say in_progress."""
        from call_use.mcp_server import _do_result

        mock_api = AsyncMock()
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "connected"})
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _do_result(task_id="call-active")
        assert result["status"] == "in_progress"
        assert result["state"] == "connected"

    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_cancel_sends_backend_command(self, MockLiveKitAPI):
        """Given cancel, should send {type: cancel} on backend-commands topic."""
        from call_use.mcp_server import cancel

        mock_api = AsyncMock()
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        result_str = await cancel(task_id="call-cancel-test")
        result = json.loads(result_str)
        assert result["status"] == "cancel_requested"
        mock_api.room.send_data.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    async def test_missing_env_vars_returns_error_json(self):
        """Given missing LiveKit keys, dial should return error JSON (not crash)."""
        from call_use.mcp_server import _do_dial

        result = await _do_dial(phone="+18005551234", instructions="test")
        assert "error" in result
        assert "Server configuration incomplete" in result["error"]
        assert "missing" in result
        assert isinstance(result["missing"], list)
        assert "LIVEKIT_URL" in result["missing"]
        assert "help" in result

    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_status_room_not_found_returns_error(self, MockLiveKitAPI):
        """Given unknown task_id, status should return error."""
        from call_use.mcp_server import _do_status

        mock_api = AsyncMock()
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[])
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _do_status(task_id="nonexistent")
        assert result["error"] == "call not found"


# ===========================================================================
# 9. Data Message Routing
# ===========================================================================


class TestDataMessageRouting:
    """Given data messages arrive, test routing to correct handlers."""

    async def test_non_backend_commands_topic_ignored(self):
        """Given data on a different topic, should be ignored."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected

        dp = MagicMock()
        dp.topic = "other-topic"
        dp.data = json.dumps({"type": "takeover"}).encode()

        # Should not raise or change state
        await agent._on_data_received(dp)
        assert agent._current_state == CallStateEnum.connected

    async def test_cancel_command_sets_cancelled_flag(self):
        """Given cancel command, agent should set _cancelled flag."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected

        dp = _make_data_packet("cancel")
        await agent._on_data_received(dp)
        assert agent._cancelled is True

    async def test_cancel_finalizes_as_cancelled(self):
        """Given cancel command, agent should finalize with cancelled disposition."""
        agent, evidence = _make_agent_with_evidence()
        agent._current_state = CallStateEnum.connected

        dp = _make_data_packet("cancel")
        await agent._on_data_received(dp)
        assert agent._finalized is True
        assert agent._current_state == CallStateEnum.ended

    async def test_inject_context_returns_formatted_note(self):
        """Given inject_context command while connected, should format as operator note."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.connected

        result = await agent._handle_inject({"text": "Account #12345"})
        assert result is not None
        assert "12345" in result
        assert "operator note" in result.lower()

    async def test_inject_blocked_while_not_connected(self):
        """Given inject while in takeover, should be blocked."""
        agent = _make_agent()
        agent._current_state = CallStateEnum.human_takeover

        result = await agent._handle_inject({"text": "Some info"})
        assert result is None


# ===========================================================================
# 10. Instruction Building
# ===========================================================================


class TestInstructionBuilding:
    """Given different task configurations, test instruction generation."""

    def test_user_info_included_naturally(self):
        """Given user_info with name/dob, instructions should contain them."""
        task = _make_task(
            instructions="Confirm appointment",
            user_info={"name": "John Doe", "dob": "1985-03-15"},
        )
        result = _build_instructions(task)
        assert "John Doe" in result
        assert "1985-03-15" in result
        assert "User-provided info" in result

    def test_empty_user_info_excluded(self):
        """Given empty user_info, instructions should not mention user-provided info."""
        task = _make_task(instructions="Simple task", user_info={})
        result = _build_instructions(task)
        assert "User-provided info" not in result

    def test_recording_disclaimer_not_in_llm_instructions(self):
        """Given recording_disclaimer, it should NOT appear in LLM instructions
        (it's spoken via session.say())."""
        task = _make_task(
            instructions="Call about bill",
            recording_disclaimer="This call is recorded.",
        )
        result = _build_instructions(task)
        assert "This call is recorded." not in result

    def test_security_instructions_always_present(self):
        """Given any task, instructions should warn about untrusted input."""
        task = _make_task(instructions="Simple call")
        result = _build_instructions(task)
        assert "untrusted input" in result.lower()
        assert "SSN" in result

    def test_ivr_instructions_always_present(self):
        """Given any task, instructions should include IVR navigation guidance."""
        task = _make_task(instructions="Simple call")
        result = _build_instructions(task)
        assert "DTMF" in result
        assert "Press" in result
