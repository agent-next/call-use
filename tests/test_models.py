"""Tests for call_use.models."""

import pytest

from call_use.models import (
    CallError,
    CallErrorCode,
    CallEvent,
    CallEventType,
    CallOutcome,
    CallStateEnum,
    CallTask,
    DispositionEnum,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# CallTask
# ---------------------------------------------------------------------------


class TestCallTask:
    def test_auto_generates_task_id(self):
        task = CallTask(phone_number="+15551234567", instructions="say hello")
        assert task.task_id.startswith("task-")
        assert len(task.task_id) == len("task-") + 8

    def test_two_tasks_get_different_ids(self):
        t1 = CallTask(phone_number="+15551234567", instructions="a")
        t2 = CallTask(phone_number="+15551234567", instructions="b")
        assert t1.task_id != t2.task_id

    def test_full_round_trip(self):
        task = CallTask(
            phone_number="+15551234567",
            caller_id="+15559999999",
            instructions="Ask about the appointment",
            user_info={"name": "Alice"},
            voice_id="voice-1",
            approval_required=False,
            timeout_seconds=300,
            recording_disclaimer="This call may be recorded.",
        )
        data = task.model_dump()
        restored = CallTask.model_validate(data)
        assert restored == task
        assert restored.caller_id == "+15559999999"
        assert restored.user_info == {"name": "Alice"}
        assert restored.approval_required is False
        assert restored.timeout_seconds == 300

    def test_defaults(self):
        task = CallTask(phone_number="+15551234567", instructions="hi")
        assert task.caller_id is None
        assert task.user_info == {}
        assert task.voice_id is None
        assert task.approval_required is True
        assert task.timeout_seconds == 600
        assert task.recording_disclaimer is None

    def test_timeout_too_low_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="timeout_seconds"):
            CallTask(phone_number="+15551234567", instructions="hi", timeout_seconds=0)

    def test_timeout_too_high_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="timeout_seconds"):
            CallTask(phone_number="+15551234567", instructions="hi", timeout_seconds=7200)

    def test_timeout_negative_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="timeout_seconds"):
            CallTask(phone_number="+15551234567", instructions="hi", timeout_seconds=-1)

    def test_timeout_at_bounds_accepted(self):
        task_low = CallTask(phone_number="+15551234567", instructions="hi", timeout_seconds=30)
        assert task_low.timeout_seconds == 30
        task_high = CallTask(phone_number="+15551234567", instructions="hi", timeout_seconds=3600)
        assert task_high.timeout_seconds == 3600


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestEnums:
    def test_call_state_enum_values(self):
        expected = {
            "created",
            "dialing",
            "ringing",
            "connected",
            "in_ivr",
            "on_hold",
            "in_conversation",
            "awaiting_approval",
            "human_takeover",
            "ended",
        }
        assert {e.value for e in CallStateEnum} == expected
        assert len(CallStateEnum) == 10

    def test_disposition_enum_values(self):
        expected = {
            "completed",
            "failed",
            "no_answer",
            "busy",
            "voicemail",
            "timeout",
            "cancelled",
        }
        assert {e.value for e in DispositionEnum} == expected
        assert len(DispositionEnum) == 7

    def test_call_event_type_values(self):
        expected = {
            "state_change",
            "transcript",
            "dtmf",
            "approval_request",
            "approval_response",
            "takeover",
            "resume",
            "error",
            "call_complete",
        }
        assert {e.value for e in CallEventType} == expected
        assert len(CallEventType) == 9

    def test_call_error_code_values(self):
        expected = {
            "dial_failed",
            "no_answer",
            "busy",
            "voicemail",
            "mid_call_drop",
            "timeout",
            "provider_error",
            "rate_limited",
            "cancelled",
        }
        assert {e.value for e in CallErrorCode} == expected
        assert len(CallErrorCode) == 9


# ---------------------------------------------------------------------------
# CallEvent
# ---------------------------------------------------------------------------


class TestCallEvent:
    def test_serializes_to_json(self):
        event = CallEvent(
            type=CallEventType.state_change,
            data={"from": "created", "to": "dialing"},
        )
        json_str = event.model_dump_json()
        assert "state_change" in json_str
        assert "dialing" in json_str

    def test_default_timestamp(self):
        event = CallEvent(type=CallEventType.transcript)
        assert isinstance(event.timestamp, float)
        assert event.timestamp > 0

    def test_default_data(self):
        event = CallEvent(type=CallEventType.error)
        assert event.data == {}


# ---------------------------------------------------------------------------
# CallOutcome
# ---------------------------------------------------------------------------


class TestCallOutcome:
    def test_has_no_success_field(self):
        assert "success" not in CallOutcome.model_fields

    def test_round_trip(self):
        outcome = CallOutcome(
            task_id="task-abcd1234",
            transcript=[{"speaker": "agent", "text": "Hello", "timestamp": 1.0}],
            events=[CallEvent(type=CallEventType.call_complete)],
            duration_seconds=42.5,
            disposition=DispositionEnum.completed,
            recording_url="https://example.com/rec.wav",
            metadata={"score": 0.95},
        )
        data = outcome.model_dump()
        restored = CallOutcome.model_validate(data)
        assert restored.task_id == "task-abcd1234"
        assert restored.duration_seconds == 42.5
        assert restored.disposition == DispositionEnum.completed
        assert restored.metadata == {"score": 0.95}


# ---------------------------------------------------------------------------
# CallError
# ---------------------------------------------------------------------------


class TestCallError:
    def test_raises_with_correct_code_and_message(self):
        with pytest.raises(CallError) as exc_info:
            raise CallError(CallErrorCode.dial_failed, "Could not connect")
        err = exc_info.value
        assert err.code == CallErrorCode.dial_failed
        assert err.message == "Could not connect"

    def test_str_includes_code(self):
        err = CallError(CallErrorCode.timeout, "Exceeded limit")
        assert str(err) == "timeout: Exceeded limit"

    def test_is_exception(self):
        assert issubclass(CallError, Exception)
