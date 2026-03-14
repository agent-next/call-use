import json
import logging
import os
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from call_use.models import (
    CallEvent,
    CallEventType,
    CallOutcome,
    CallStateEnum,
    CallTask,
    DispositionEnum,
)

logger = logging.getLogger(__name__)
LOGS_DIR = Path(os.environ.get("CALL_USE_LOG_DIR", Path.home() / ".call-use" / "logs"))


class EvidencePipeline:
    def __init__(
        self, task: CallTask, room_name: str | None = None, agent_identity: str | None = None
    ):
        self.task = task
        self._room_name = room_name  # For room metadata writes; None in tests
        self._agent_identity = agent_identity
        self._events: list[CallEvent] = []
        self._transcript: list[dict] = []  # [{speaker, text, timestamp}]
        self._started_at: float = time.time()
        self._subscribers: list[Callable[[CallEvent], Awaitable[None]]] = []

    def subscribe(self, callback: Callable[[CallEvent], Awaitable[None]]):
        """Register async event subscriber."""
        self._subscribers.append(callback)

    async def emit(self, event: CallEvent):
        """Record event internally AND notify all subscribers.
        Subscriber errors are caught and logged -- never break the pipeline."""
        self._events.append(event)
        for sub in self._subscribers:
            try:
                await sub(event)
            except Exception:
                logger.warning("Subscriber error", exc_info=True)

    async def emit_state_change(self, old: CallStateEnum, new: CallStateEnum):
        """Emit a state_change event. Does NOT write room metadata (that's the agent's job)."""
        await self.emit(
            CallEvent(
                type=CallEventType.state_change,
                data={"from": old.value, "to": new.value},
            )
        )

    async def emit_transcript(self, speaker: str, text: str):
        """Emit transcript event and also append to _transcript list."""
        entry = {"speaker": speaker, "text": text, "timestamp": time.time()}
        self._transcript.append(entry)
        await self.emit(
            CallEvent(
                type=CallEventType.transcript,
                data=entry,
            )
        )

    async def emit_dtmf(self, keys: str):
        await self.emit(CallEvent(type=CallEventType.dtmf, data={"keys": keys}))

    async def emit_approval_request(self, approval_id: str, details: str, agent_identity: str):
        await self.emit(
            CallEvent(
                type=CallEventType.approval_request,
                data={
                    "approval_id": approval_id,
                    "details": details,
                    "agent_identity": agent_identity,
                },
            )
        )

    async def emit_approval_response(self, approval_id: str, result: str):
        await self.emit(
            CallEvent(
                type=CallEventType.approval_response,
                data={"approval_id": approval_id, "result": result},
            )
        )

    async def emit_takeover(self):
        await self.emit(CallEvent(type=CallEventType.takeover, data={}))

    async def emit_resume(self):
        await self.emit(CallEvent(type=CallEventType.resume, data={}))

    async def emit_error(self, code: str, message: str):
        await self.emit(
            CallEvent(
                type=CallEventType.error,
                data={"code": code, "message": message},
            )
        )

    def finalize(self, disposition: DispositionEnum) -> CallOutcome:
        """Build CallOutcome and write JSON log file."""
        outcome = CallOutcome(
            task_id=self.task.task_id,
            transcript=list(self._transcript),
            events=list(self._events),
            duration_seconds=time.time() - self._started_at,
            disposition=disposition,
            metadata={
                "phone_number": self.task.phone_number,
                "caller_id": self.task.caller_id,
            },
        )
        # Write JSON log
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOGS_DIR / f"{self.task.task_id}.json"
            with open(log_path, "w") as f:
                json.dump(outcome.model_dump(mode="json"), f, indent=2)
        except Exception:
            logger.warning("Failed to write log file", exc_info=True)
        return outcome
