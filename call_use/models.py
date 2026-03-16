"""Pydantic v2 models for the call-use package."""

from __future__ import annotations

import time
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# CallTask
# ---------------------------------------------------------------------------


def _generate_task_id() -> str:
    return f"task-{uuid4().hex[:8]}"


class CallTask(BaseModel):
    """Configuration for an outbound phone call task."""

    task_id: str = Field(default_factory=_generate_task_id)
    phone_number: str  # E.164
    caller_id: str | None = None
    instructions: str
    user_info: dict = Field(default_factory=dict)
    voice_id: str | None = None
    approval_required: bool = True
    timeout_seconds: int = Field(default=600, ge=30, le=3600)
    recording_disclaimer: str | None = None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CallStateEnum(str, Enum):
    """Possible states of a call during its lifecycle."""

    created = "created"
    dialing = "dialing"
    ringing = "ringing"
    connected = "connected"
    in_ivr = "in_ivr"
    on_hold = "on_hold"
    in_conversation = "in_conversation"
    awaiting_approval = "awaiting_approval"
    human_takeover = "human_takeover"
    ended = "ended"


class DispositionEnum(str, Enum):
    """Final outcome classification of a completed call."""

    completed = "completed"
    failed = "failed"
    no_answer = "no_answer"
    busy = "busy"
    voicemail = "voicemail"
    timeout = "timeout"
    cancelled = "cancelled"
    error = "error"


class CallEventType(str, Enum):
    """Types of events emitted during a call lifecycle."""

    state_change = "state_change"
    transcript = "transcript"
    dtmf = "dtmf"
    approval_request = "approval_request"
    approval_response = "approval_response"
    takeover = "takeover"
    resume = "resume"
    error = "error"
    call_complete = "call_complete"


class CallErrorCode(str, Enum):
    """Structured error codes for programmatic error handling."""

    dial_failed = "dial_failed"
    no_answer = "no_answer"
    busy = "busy"
    voicemail = "voicemail"
    mid_call_drop = "mid_call_drop"
    timeout = "timeout"
    provider_error = "provider_error"
    rate_limited = "rate_limited"
    cancelled = "cancelled"
    worker_not_running = "worker_not_running"
    configuration_error = "configuration_error"


# ---------------------------------------------------------------------------
# Event / Outcome models
# ---------------------------------------------------------------------------


class CallEvent(BaseModel):
    """A single event emitted during a call lifecycle."""

    timestamp: float = Field(default_factory=time.time)
    type: CallEventType
    data: dict = Field(default_factory=dict)


class CallOutcome(BaseModel):
    """Result of a completed phone call, including transcript and disposition."""

    task_id: str
    transcript: list[dict]  # [{speaker, text, timestamp}]
    events: list[CallEvent]
    duration_seconds: float
    disposition: DispositionEnum
    recording_url: str | None = None
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# CallError
# ---------------------------------------------------------------------------


class CallError(Exception):
    """Structured error raised by call-use operations."""

    def __init__(self, code: CallErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
