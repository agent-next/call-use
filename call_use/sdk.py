"""call-use SDK — public CallAgent class for making outbound calls."""

import asyncio
import json
import logging
import os
import time
from collections.abc import Callable
from datetime import timedelta

from livekit import api, rtc
from livekit.api import LiveKitAPI, SendDataRequest
from livekit.protocol.models import DataPacket

from call_use.models import (
    CallError,
    CallErrorCode,
    CallEvent,
    CallEventType,
    CallOutcome,
    CallTask,
    DispositionEnum,
)
from call_use.phone import validate_caller_id, validate_phone_number

WORKER_JOIN_TIMEOUT = 10  # seconds to wait for worker to join room

logger = logging.getLogger(__name__)


async def _get_agent_identity(lkapi: LiveKitAPI, room_name: str) -> str:
    """Look up agent participant identity from room metadata."""
    rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
    if not rooms.rooms:
        raise RuntimeError(f"Room {room_name} not found")
    metadata = json.loads(rooms.rooms[0].metadata or "{}")
    agent_id = metadata.get("agent_identity")
    if not agent_id:
        raise RuntimeError("Agent not yet initialized")
    return str(agent_id)


class CallAgent:
    """High-level SDK entry point for making outbound calls.

    Usage:
        agent = CallAgent(
            phone="+18001234567",
            instructions="Cancel my internet subscription",
            on_event=lambda e: print(e),
            on_approval=lambda details: "approved",
        )
        outcome = await agent.call()
    """

    def __init__(
        self,
        phone: str,
        instructions: str,
        user_info: dict | None = None,
        caller_id: str | None = None,
        voice_id: str | None = None,
        approval_required: bool = True,
        timeout_seconds: int = 600,
        on_event: Callable[[CallEvent], None] | None = None,
        on_approval: Callable[[dict], str] | None = None,
        recording_disclaimer: str | None = None,
    ):
        """Initialize a CallAgent for making an outbound call.

        Args:
            phone: Target phone number in E.164 format.
            instructions: Natural-language instructions for the agent.
            user_info: Optional context dict passed to the agent.
            caller_id: Optional outbound caller ID in E.164 format.
            voice_id: Optional voice identifier for TTS.
            approval_required: Whether the agent must request approval before acting.
            timeout_seconds: Maximum call duration in seconds.
            on_event: Optional callback invoked for every call event.
            on_approval: Callback invoked when the agent requests approval.
            recording_disclaimer: Optional disclaimer played at the start of the call.

        Raises:
            ValueError: If phone number is invalid or if approval_required=True
                without an on_approval callback.
        """
        if approval_required and on_approval is None:
            raise ValueError(
                "on_approval callback is required when approval_required=True. "
                "Either provide on_approval or set approval_required=False."
            )
        if not (30 <= timeout_seconds <= 3600):
            raise ValueError(f"timeout_seconds must be between 30 and 3600, got {timeout_seconds}")
        self._phone = validate_phone_number(phone)
        self._caller_id = validate_caller_id(caller_id)
        self._instructions = instructions
        self._user_info = user_info or {}
        self._voice_id = voice_id
        self._approval_required = approval_required
        self._timeout_seconds = timeout_seconds
        self._on_event = on_event
        self._on_approval = on_approval
        self._recording_disclaimer = recording_disclaimer
        self._room_name: str | None = None

    async def call(self) -> CallOutcome:
        """Execute the call and return the outcome.

        Raises:
            RuntimeError: If required environment variables (LIVEKIT_API_KEY,
                LIVEKIT_API_SECRET, LIVEKIT_URL) are missing.
        """
        self._room_name = None

        required_vars = [
            "LIVEKIT_URL",
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
            "SIP_TRUNK_ID",
            "OPENAI_API_KEY",
        ]
        missing = [v for v in required_vars if v not in os.environ]
        if missing:
            raise CallError(
                CallErrorCode.configuration_error,
                f"Missing required environment variables: {', '.join(missing)}",
            )

        task = CallTask(
            phone_number=self._phone,
            caller_id=self._caller_id,
            instructions=self._instructions,
            user_info=self._user_info,
            voice_id=self._voice_id,
            approval_required=self._approval_required,
            timeout_seconds=self._timeout_seconds,
            recording_disclaimer=self._recording_disclaimer,
        )

        start_time = time.time()
        room_name = task.task_id
        self._room_name = room_name
        room = rtc.Room()
        call_complete = asyncio.Event()
        worker_joined = asyncio.Event()
        outcome_holder: list[CallOutcome | None] = [None]

        # Register participant handler BEFORE connecting
        @room.on("participant_connected")
        def _on_participant(participant):
            identity = getattr(participant, "identity", "") or ""
            if identity.startswith("call-use-agent-"):
                worker_joined.set()

        # Register data handler BEFORE connecting
        @room.on("data_received")
        def _on_data(dp):
            if dp.topic != "call-events":
                return
            event_data = json.loads(dp.data.decode("utf-8"))
            try:
                event = CallEvent(**event_data)
            except (TypeError, ValueError) as exc:
                logger.error("Failed to parse CallEvent (raw data: %s): %s", event_data, exc)
                return

            if self._on_event:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, self._on_event, event)

            if event.type == CallEventType.call_complete:
                try:
                    outcome_holder[0] = CallOutcome(**event.data)
                except (TypeError, ValueError) as exc:
                    logger.error(
                        "Failed to parse CallOutcome (raw data: %s): %s",
                        event.data,
                        exc,
                        exc_info=True,
                    )
                    fallback_id = (
                        event.data.get("task_id", "unknown")
                        if isinstance(event.data, dict)
                        else "unknown"
                    )
                    outcome_holder[0] = CallOutcome(
                        task_id=fallback_id,
                        transcript=[],
                        events=[],
                        duration_seconds=0,
                        disposition=DispositionEnum.error,
                    )
                call_complete.set()
                return

            if event.type == CallEventType.approval_request and self._on_approval:

                async def _handle_approval():
                    loop = asyncio.get_running_loop()
                    assert self._on_approval is not None
                    result = await loop.run_in_executor(None, self._on_approval, event.data)
                    await self._send_approval_response(
                        room_name,
                        event.data.get("approval_id"),
                        result,
                    )

                asyncio.create_task(_handle_approval())

        # Join room as SDK monitor
        sdk_token = api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
        sdk_token.with_identity(f"sdk-{task.task_id[:8]}")
        sdk_token.with_ttl(timedelta(hours=2))
        sdk_token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_subscribe=True,
                can_publish=False,
                can_publish_data=False,
            )
        )
        await room.connect(os.environ["LIVEKIT_URL"], sdk_token.to_jwt())

        try:
            # Dispatch agent
            metadata = json.dumps(task.model_dump(mode="json"))
            async with LiveKitAPI() as lkapi:
                await lkapi.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name="call-use-agent",
                        room=room_name,
                        metadata=metadata,
                    )
                )

            # Wait for worker to pick up the job
            if not worker_joined.is_set():
                try:
                    await asyncio.wait_for(worker_joined.wait(), timeout=WORKER_JOIN_TIMEOUT)
                except asyncio.TimeoutError:
                    raise CallError(
                        code=CallErrorCode.worker_not_running,
                        message=(
                            "No call-use-worker picked up the job within "
                            f"{WORKER_JOIN_TIMEOUT}s. "
                            "Ensure the worker is running: call-use-worker start"
                        ),
                    )

            # Wait for call to complete
            try:
                await asyncio.wait_for(call_complete.wait(), timeout=self._timeout_seconds + 30)
            except asyncio.TimeoutError:
                pass

            outcome = outcome_holder[0]

            # Fallback: read from room metadata
            if outcome is None:
                try:
                    async with LiveKitAPI() as lkapi:
                        rooms_resp = await lkapi.room.list_rooms(
                            api.ListRoomsRequest(names=[room_name])
                        )
                        if rooms_resp.rooms and rooms_resp.rooms[0].metadata:
                            meta = json.loads(rooms_resp.rooms[0].metadata)
                            if "outcome" in meta:
                                outcome = CallOutcome(**meta["outcome"])
                except Exception:
                    logger.warning("Failed to read outcome from metadata", exc_info=True)

            if outcome is None:
                outcome = CallOutcome(
                    task_id=task.task_id,
                    transcript=[],
                    events=[],
                    duration_seconds=time.time() - start_time,
                    disposition=DispositionEnum.timeout,
                )

            return outcome
        finally:
            await room.disconnect()

    async def takeover(self) -> str:
        """Request human takeover. Returns JWT token for human to join the room."""
        await self._send_command("takeover")
        if self._room_name is None:
            raise RuntimeError("Call not started; room name unavailable")
        token = api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
        token.with_identity(f"human-{self._room_name[:8]}")
        token.with_ttl(timedelta(minutes=15))
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=self._room_name,
                can_subscribe=True,
                can_publish=True,
                can_publish_data=False,
            )
        )
        return token.to_jwt()  # type: ignore[no-any-return]

    async def resume(self):
        """Resume agent control after human takeover."""
        await self._send_command("resume")

    async def cancel(self):
        """Cancel the active call."""
        await self._send_command("cancel")

    async def _send_command(self, cmd_type: str):
        """Send a control command to the agent."""
        if not self._room_name:
            raise RuntimeError("No active call")
        async with LiveKitAPI() as lkapi:
            agent_id = await _get_agent_identity(lkapi, self._room_name)
            await lkapi.room.send_data(
                SendDataRequest(
                    room=self._room_name,
                    data=json.dumps({"type": cmd_type}).encode(),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )

    async def _send_approval_response(self, room_name, approval_id, result):
        """Send approval response to agent."""
        cmd_type = "approve" if result == "approved" else "reject"
        async with LiveKitAPI() as lkapi:
            agent_id = await _get_agent_identity(lkapi, room_name)
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps(
                        {
                            "type": cmd_type,
                            "approval_id": approval_id,
                        }
                    ).encode(),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
