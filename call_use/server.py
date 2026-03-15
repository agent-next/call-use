"""call-use dispatch server — FastAPI endpoints for call control."""

import asyncio
import hmac
import json
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from livekit import api
from livekit.api import LiveKitAPI, SendDataRequest
from livekit.protocol.models import DataPacket
from pydantic import BaseModel, Field

from call_use.phone import validate_caller_id, validate_phone_number
from call_use.rate_limit import RateLimiter


class InjectRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class CreateCallRequest(BaseModel):
    phone_number: str
    instructions: str = Field(default="Have a friendly conversation", max_length=5000)
    caller_id: str | None = None
    user_info: dict = Field(default_factory=dict)
    voice_id: str | None = Field(default=None, pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")
    approval_required: bool = True
    timeout_seconds: int = Field(default=600, ge=30, le=3600)
    recording_disclaimer: str | None = Field(default=None, max_length=500)


class CreateCallResponse(BaseModel):
    task_id: str
    status: str
    room_name: str
    livekit_token: str


class CallStatusResponse(BaseModel):
    task_id: str
    state: str
    participants: list[str]


def create_app(api_key: str | None = None) -> FastAPI:
    """Create Call-Use FastAPI application."""
    api_key = api_key or os.environ.get("API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY required")

    app = FastAPI(title="Call-Use API")

    # In-memory call registry (call_id → room_name)
    # WARNING: This state is lost on server restart. For production deployments,
    # use a persistent store (Redis, database) or rely on LiveKit room metadata
    # for call state recovery.
    call_rooms: dict[str, str] = {}
    _call_locks: dict[str, asyncio.Lock] = {}

    rate_limiter = RateLimiter(
        max_calls=int(os.environ.get("RATE_LIMIT_MAX", "10")),
        window_seconds=int(os.environ.get("RATE_LIMIT_WINDOW", "3600")),
    )

    def _get_call_lock(call_id: str) -> asyncio.Lock:
        if call_id not in _call_locks:
            _call_locks[call_id] = asyncio.Lock()
        return _call_locks[call_id]

    async def verify_api_key_dep(x_api_key: str = Header()):
        if not hmac.compare_digest(x_api_key, api_key):
            raise HTTPException(401, "Invalid API key")
        return x_api_key

    async def _get_agent_identity(lkapi: LiveKitAPI, room_name: str) -> str:
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
        if not rooms.rooms:
            raise HTTPException(404, f"Room {room_name} not found")
        metadata = json.loads(rooms.rooms[0].metadata or "{}")
        agent_id = metadata.get("agent_identity")
        if not agent_id:
            raise HTTPException(409, "Agent not yet initialized")
        return str(agent_id)

    async def _get_room_state(lkapi: LiveKitAPI, room_name: str) -> str:
        rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
        if not rooms.rooms:
            raise HTTPException(404, "Room not found")
        metadata = json.loads(rooms.rooms[0].metadata or "{}")
        return str(metadata.get("state", "unknown"))

    def _get_room_name(call_id: str) -> str:
        room_name = call_rooms.get(call_id)
        if not room_name:
            raise HTTPException(404, f"Call {call_id} not found")
        return room_name

    @app.post("/calls", dependencies=[Depends(verify_api_key_dep)])
    async def create_call(req: CreateCallRequest, x_api_key: str = Header()):
        # Rate limit
        if not rate_limiter.check(x_api_key):
            raise HTTPException(
                429,
                f"Rate limit exceeded. Max {rate_limiter.max_calls} calls"
                f" per {rate_limiter.window_seconds}s.",
            )

        # Validate phone number
        try:
            phone_number = validate_phone_number(req.phone_number)
        except ValueError as e:
            raise HTTPException(400, str(e))

        # Validate caller_id
        caller_id = req.caller_id
        if caller_id:
            try:
                caller_id = validate_caller_id(caller_id)
            except ValueError as e:
                raise HTTPException(400, str(e))

        task_id = "call-" + secrets.token_hex(6)
        room_name = task_id

        metadata = json.dumps(
            {
                "phone_number": phone_number,
                "caller_id": caller_id,
                "instructions": req.instructions,
                "user_info": req.user_info,
                "voice_id": req.voice_id,
                "approval_required": req.approval_required,
                "timeout_seconds": req.timeout_seconds,
                "recording_disclaimer": req.recording_disclaimer,
            }
        )

        async with LiveKitAPI() as lkapi:
            await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name="call-use-agent",
                    room=room_name,
                    metadata=metadata,
                )
            )

        call_rooms[task_id] = room_name

        # Generate subscribe-only monitor token
        monitor_token = api.AccessToken(
            os.environ.get("LIVEKIT_API_KEY", ""),
            os.environ.get("LIVEKIT_API_SECRET", ""),
        )
        monitor_token.with_identity(f"monitor-{task_id}")
        monitor_token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_subscribe=True,
                can_publish=False,
                can_publish_data=False,
            )
        )

        return CreateCallResponse(
            task_id=task_id,
            status="dialing",
            room_name=room_name,
            livekit_token=monitor_token.to_jwt(),
        )

    @app.get("/calls/{call_id}", dependencies=[Depends(verify_api_key_dep)])
    async def get_call(call_id: str):
        room_name = _get_room_name(call_id)
        async with LiveKitAPI() as lkapi:
            state = await _get_room_state(lkapi, room_name)
            rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
            participants = []
            if rooms.rooms:
                parts = await lkapi.room.list_participants(
                    api.ListParticipantsRequest(room=room_name)
                )
                participants = [p.identity for p in parts.participants]
        return CallStatusResponse(
            task_id=call_id,
            state=state,
            participants=participants,
        )

    @app.post("/calls/{call_id}/inject", dependencies=[Depends(verify_api_key_dep)])
    async def inject_message(call_id: str, body: InjectRequest):
        room_name = _get_room_name(call_id)
        async with _get_call_lock(call_id), LiveKitAPI() as lkapi:
            agent_id = await _get_agent_identity(lkapi, room_name)
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps({"type": "inject_context", "text": body.message}).encode("utf-8"),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
        return {"status": "sent"}

    @app.post("/calls/{call_id}/takeover", dependencies=[Depends(verify_api_key_dep)])
    async def takeover(call_id: str):
        room_name = _get_room_name(call_id)
        async with _get_call_lock(call_id), LiveKitAPI() as lkapi:
            agent_id = await _get_agent_identity(lkapi, room_name)
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps({"type": "takeover"}).encode("utf-8"),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
            # Poll for agent ack
            for _ in range(20):
                await asyncio.sleep(0.1)
                rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
                if not rooms.rooms:
                    raise HTTPException(404, "Room closed during takeover")
                meta = json.loads(rooms.rooms[0].metadata or "{}")
                if meta.get("state") == "human_takeover":
                    break
            else:
                raise HTTPException(504, "Takeover ack timed out")

            # Generate takeover token with publish permissions
            takeover_token = api.AccessToken(
                os.environ.get("LIVEKIT_API_KEY", ""),
                os.environ.get("LIVEKIT_API_SECRET", ""),
            )
            takeover_token.with_identity("supervisor")
            takeover_token.with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_subscribe=True,
                    can_publish=True,
                    can_publish_data=False,
                )
            )

        return {"status": "takeover_active", "takeover_token": takeover_token.to_jwt()}

    @app.post("/calls/{call_id}/resume", dependencies=[Depends(verify_api_key_dep)])
    async def resume(call_id: str, body: dict):
        room_name = _get_room_name(call_id)
        summary = body.get("summary", "")
        async with _get_call_lock(call_id), LiveKitAPI() as lkapi:
            agent_id = await _get_agent_identity(lkapi, room_name)
            state = await _get_room_state(lkapi, room_name)
            if state == "connected":
                return {"status": "already_active"}
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps({"type": "resume", "summary": summary}).encode("utf-8"),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
            for _ in range(20):
                await asyncio.sleep(0.1)
                rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
                if not rooms.rooms:
                    raise HTTPException(404, "Room closed during resume")
                meta = json.loads(rooms.rooms[0].metadata or "{}")
                if meta.get("state") == "connected":
                    break
            else:
                raise HTTPException(504, "Resume ack timed out")
            # Revoke supervisor publish
            try:
                await lkapi.room.update_participant(
                    api.UpdateParticipantRequest(
                        room=room_name,
                        identity="supervisor",
                        permission=api.ParticipantPermission(
                            can_subscribe=True,
                            can_publish=False,
                            can_publish_data=False,
                        ),
                    )
                )
            except Exception:
                pass
        return {"status": "ai_resumed"}

    @app.post("/calls/{call_id}/approve", dependencies=[Depends(verify_api_key_dep)])
    async def approve_decision(call_id: str):
        room_name = _get_room_name(call_id)
        async with _get_call_lock(call_id), LiveKitAPI() as lkapi:
            rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
            if not rooms.rooms:
                raise HTTPException(404, "Room not found")
            meta = json.loads(rooms.rooms[0].metadata or "{}")
            agent_id = meta.get("agent_identity")
            if not agent_id:
                raise HTTPException(409, "Agent not yet initialized")
            approval_id = meta.get("approval_id")
            if not approval_id:
                raise HTTPException(409, "No pending approval")
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps({"type": "approve", "approval_id": approval_id}).encode(
                        "utf-8"
                    ),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
        return {"status": "sent_approve", "approval_id": approval_id}

    @app.post("/calls/{call_id}/reject", dependencies=[Depends(verify_api_key_dep)])
    async def reject_decision(call_id: str):
        room_name = _get_room_name(call_id)
        async with _get_call_lock(call_id), LiveKitAPI() as lkapi:
            rooms = await lkapi.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
            if not rooms.rooms:
                raise HTTPException(404, "Room not found")
            meta = json.loads(rooms.rooms[0].metadata or "{}")
            agent_id = meta.get("agent_identity")
            if not agent_id:
                raise HTTPException(409, "Agent not yet initialized")
            approval_id = meta.get("approval_id")
            if not approval_id:
                raise HTTPException(409, "No pending approval")
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps({"type": "reject", "approval_id": approval_id}).encode("utf-8"),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
        return {"status": "sent_reject", "approval_id": approval_id}

    @app.post("/calls/{call_id}/cancel", dependencies=[Depends(verify_api_key_dep)])
    async def cancel_call(call_id: str):
        room_name = _get_room_name(call_id)
        async with _get_call_lock(call_id), LiveKitAPI() as lkapi:
            agent_id = await _get_agent_identity(lkapi, room_name)
            await lkapi.room.send_data(
                SendDataRequest(
                    room=room_name,
                    data=json.dumps({"type": "cancel"}).encode("utf-8"),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                    destination_identities=[agent_id],
                )
            )
        return {"status": "cancelling", "call_id": call_id}

    return app
