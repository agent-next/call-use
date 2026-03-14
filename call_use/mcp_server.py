"""call-use MCP server — expose phone calling as tools for AI agents.

Architecture: Non-blocking async design.
- dial: creates room + dispatches agent via agent_dispatch API, returns task_id immediately
- status: polls room metadata for call state (agent writes "state" field)
- cancel: sends cancel command via data channel (topic: backend-commands, type: cancel)
- result: retrieves final CallOutcome from room metadata after call ends (state: ended)
"""

import json
import logging
import os
import uuid

from livekit.api import (
    CreateAgentDispatchRequest,
    CreateRoomRequest,
    DataPacket,
    ListRoomsRequest,
    LiveKitAPI,
    SendDataRequest,
)
from mcp.server import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "call-use",
    instructions=(
        "Give your AI agent the ability to make phone calls. The 'browser-use' for phones."
    ),
)


async def _do_dial(
    phone: str,
    instructions: str,
    user_info: dict | None = None,
    caller_id: str | None = None,
    voice_id: str | None = None,
    timeout: int = 600,
) -> dict:
    """Dispatch a call via LiveKit and return immediately with task_id."""
    required = {
        "LIVEKIT_URL": "LiveKit server URL (wss://...)",
        "LIVEKIT_API_KEY": "LiveKit API key",
        "LIVEKIT_API_SECRET": "LiveKit API secret",
        "SIP_TRUNK_ID": "Twilio SIP trunk ID in LiveKit",
        "OPENAI_API_KEY": "OpenAI API key (for STT + LLM + TTS)",
    }
    missing = [f"{k} — {v}" for k, v in required.items() if not os.environ.get(k)]
    if missing:
        return {
            "error": "Missing required environment variables",
            "missing": missing,
            "help": "https://github.com/agent-next/call-use#configure",
        }

    task_id = f"call-{uuid.uuid4().hex[:12]}"

    async with LiveKitAPI() as lk:
        await lk.room.create_room(
            CreateRoomRequest(
                name=task_id,
                empty_timeout=timeout + 60,
            )
        )

        metadata = json.dumps(
            {
                "phone_number": phone,
                "instructions": instructions,
                "user_info": user_info or {},
                "caller_id": caller_id,
                "voice_id": voice_id,
                "timeout_seconds": timeout,
                "approval_required": False,
            }
        )
        await lk.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name="call-use-agent",
                room=task_id,
                metadata=metadata,
            )
        )

    return {"task_id": task_id, "status": "dispatched"}


async def _do_status(task_id: str) -> dict:
    """Poll room metadata for call state."""
    async with LiveKitAPI() as lk:
        rooms = await lk.room.list_rooms(ListRoomsRequest(names=[task_id]))
        if not rooms.rooms:
            return {"task_id": task_id, "error": "call not found"}

        room = rooms.rooms[0]
        metadata = json.loads(room.metadata) if room.metadata else {}
        return {
            "task_id": task_id,
            "state": metadata.get("state", "unknown"),
        }


async def _do_result(task_id: str) -> dict:
    """Retrieve final CallOutcome from room metadata."""
    async with LiveKitAPI() as lk:
        rooms = await lk.room.list_rooms(ListRoomsRequest(names=[task_id]))
        if not rooms.rooms:
            return {"task_id": task_id, "error": "call not found"}

        room = rooms.rooms[0]
        metadata = json.loads(room.metadata) if room.metadata else {}

        if metadata.get("state") == "ended" and "outcome" in metadata:
            return dict(metadata["outcome"])

        return {
            "task_id": task_id,
            "status": "in_progress",
            "state": metadata.get("state", "unknown"),
        }


@mcp.tool()
async def dial(
    phone: str,
    instructions: str,
    user_info: str | None = None,
    caller_id: str | None = None,
    voice_id: str | None = None,
    timeout: int = 600,
) -> str:
    """Dispatch an outbound phone call via AI agent. Returns immediately with a task_id.

    The call runs asynchronously. Use 'status' to poll progress, 'cancel' to abort,
    and 'result' to retrieve the final outcome once the call completes.

    Args:
        phone: Target phone number in E.164 format (e.g., +18001234567). US/Canada only.
        instructions: What the agent should accomplish on the call.
        user_info: Optional JSON string with context for the agent.
        caller_id: Optional outbound caller ID in E.164 format.
        voice_id: TTS voice: alloy, echo, fable, onyx, nova, shimmer. Default: alloy.
        timeout: Max call duration in seconds. Default: 600.

    Returns:
        JSON with task_id and status ("dispatched"). Use 'status' tool to poll.
    """
    parsed_info = None
    if user_info:
        try:
            parsed_info = json.loads(user_info)
        except json.JSONDecodeError:
            return json.dumps({"error": "user_info must be valid JSON"})
        if not isinstance(parsed_info, dict):
            return json.dumps(
                {"error": "user_info must be a JSON object (dict), not array or scalar"}
            )

    try:
        result = await _do_dial(
            phone=phone,
            instructions=instructions,
            user_info=parsed_info,
            caller_id=caller_id,
            voice_id=voice_id,
            timeout=timeout,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def status(task_id: str) -> str:
    """Check the current state of a phone call.

    Args:
        task_id: The task_id returned by the 'dial' tool.
    """
    try:
        result = await _do_status(task_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "task_id": task_id})


@mcp.tool()
async def cancel(task_id: str) -> str:
    """Cancel an active phone call.

    Args:
        task_id: The task_id of the call to cancel.
    """
    try:
        async with LiveKitAPI() as lk:
            await lk.room.send_data(
                SendDataRequest(
                    room=task_id,
                    data=json.dumps({"type": "cancel"}).encode(),
                    kind=DataPacket.Kind.RELIABLE,
                    topic="backend-commands",
                )
            )
        return json.dumps({"task_id": task_id, "status": "cancel_requested"})
    except Exception as e:
        return json.dumps({"error": str(e), "task_id": task_id})


@mcp.tool()
async def result(task_id: str) -> str:
    """Retrieve the final outcome of a completed phone call.

    Call this after 'status' shows the call has finished.

    Args:
        task_id: The task_id returned by the 'dial' tool.
    """
    try:
        outcome = await _do_result(task_id)
        return json.dumps(outcome, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "task_id": task_id})


def main():
    """CLI entrypoint for call-use MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
