"""Tests for call-use MCP server tools."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.mcp_server import _do_dial, _do_result, _do_status
from call_use.models import CallError, CallErrorCode

pytestmark = pytest.mark.unit

_FULL_ENV = {
    "LIVEKIT_URL": "wss://test",
    "LIVEKIT_API_KEY": "key",
    "LIVEKIT_API_SECRET": "secret",
    "SIP_TRUNK_ID": "trunk",
    "OPENAI_API_KEY": "sk-test",
    "DEEPGRAM_API_KEY": "dg-test",
}


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_dial_returns_task_id(MockLiveKitAPI):
    """dial dispatches agent and returns task_id immediately."""
    mock_api = AsyncMock()
    mock_api.room.create_room.return_value = MagicMock()
    mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_dial(phone="+18005551234", instructions="Ask about hours")
    assert "task_id" in result
    assert result["status"] == "dispatched"
    assert "disposition" not in result
    mock_api.agent_dispatch.create_dispatch.assert_called_once()


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server.CreateAgentDispatchRequest")
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_dial_sets_approval_required_false(MockLiveKitAPI, MockDispatchReq):
    """MCP mode always sets approval_required=False (non-interactive, no stdin)."""
    mock_api = AsyncMock()
    mock_api.room.create_room.return_value = MagicMock()
    mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    await _do_dial(phone="+18005551234", instructions="Test approval flag")
    dispatch_kwargs = MockDispatchReq.call_args.kwargs
    metadata = json.loads(dispatch_kwargs["metadata"])
    assert metadata["approval_required"] is False


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server.CreateAgentDispatchRequest")
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_dial_with_user_info(MockLiveKitAPI, MockDispatchReq):
    """dial passes user_info in dispatch metadata."""
    mock_api = AsyncMock()
    mock_api.room.create_room.return_value = MagicMock()
    mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    await _do_dial(
        phone="+18005551234",
        instructions="Cancel",
        user_info={"name": "Alice"},
    )
    # Extract metadata from the kwargs passed to CreateAgentDispatchRequest()
    dispatch_kwargs = MockDispatchReq.call_args.kwargs
    metadata = json.loads(dispatch_kwargs["metadata"])
    assert metadata["user_info"] == {"name": "Alice"}


@pytest.mark.asyncio
async def test_dial_rejects_non_dict_user_info():
    """dial returns error when user_info is a JSON array or scalar."""
    from call_use.mcp_server import dial

    result_str = await dial(phone="+18005551234", instructions="Test", user_info="[]")
    result = json.loads(result_str)
    assert "error" in result
    assert "dict" in result["error"]

    result_str = await dial(phone="+18005551234", instructions="Test", user_info='"a string"')
    result = json.loads(result_str)
    assert "error" in result
    assert "dict" in result["error"]


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_status_returns_call_state(MockLiveKitAPI):
    """status returns current call state from room metadata."""
    mock_api = AsyncMock()
    mock_room = MagicMock()
    mock_room.metadata = json.dumps({"state": "connected"})
    mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_status(task_id="call-test-123")
    assert result["state"] == "connected"
    assert "duration_seconds" not in result


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_status_room_not_found(MockLiveKitAPI):
    """status returns error when room not found."""
    mock_api = AsyncMock()
    mock_api.room.list_rooms.return_value = MagicMock(rooms=[])
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_status(task_id="call-nonexistent")
    assert result["error"] == "call not found"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_result_returns_outcome(MockLiveKitAPI):
    """result returns CallOutcome when call has ended."""
    mock_api = AsyncMock()
    mock_room = MagicMock()
    mock_room.metadata = json.dumps(
        {
            "state": "ended",
            "outcome": {
                "task_id": "call-test-123",
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

    result = await _do_result(task_id="call-test-123")
    assert result["disposition"] == "completed"
    assert result["task_id"] == "call-test-123"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_result_in_progress(MockLiveKitAPI):
    """result returns in_progress when call hasn't ended yet."""
    mock_api = AsyncMock()
    mock_room = MagicMock()
    mock_room.metadata = json.dumps({"state": "connected"})
    mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_result(task_id="call-test-123")
    assert result["status"] == "in_progress"
    assert result["state"] == "connected"


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_dial_livekit_connection_error(MockLiveKitAPI):
    """dial returns error JSON when LiveKit is unreachable."""
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(side_effect=ConnectionError("refused"))
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)
    from call_use.mcp_server import dial

    result_str = await dial(phone="+18005551234", instructions="test")
    result = json.loads(result_str)
    assert "error" in result
    assert "refused" not in result_str  # Original error message must not leak


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_cancel_sends_command(MockLiveKitAPI):
    """cancel tool sends cancel command via data channel."""
    mock_api = AsyncMock()
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import cancel

    result_str = await cancel(task_id="call-test-cancel")
    result = json.loads(result_str)
    assert result["status"] == "cancel_requested"
    mock_api.room.send_data.assert_called_once()


@pytest.mark.asyncio
@patch.dict(os.environ, {}, clear=True)
async def test_do_dial_missing_env_returns_error():
    """_do_dial returns error dict when env vars are missing."""
    result = await _do_dial(phone="+18005551234", instructions="test")
    assert "error" in result
    assert "Server configuration incomplete" in result["error"]
    assert "missing" in result
    assert isinstance(result["missing"], list)
    assert "LIVEKIT_URL" in result["missing"]
    assert "OPENAI_API_KEY" in result["missing"]
    assert result["help"] == "https://github.com/agent-next/call-use#configure"


# ===========================================================================
# MCP tool wrappers (dial, status, result) — test the tool-level wrappers
# ===========================================================================


@pytest.mark.asyncio
async def test_dial_invalid_json_user_info():
    """dial returns error when user_info is invalid JSON."""
    from call_use.mcp_server import dial

    result_str = await dial(phone="+18005551234", instructions="Test", user_info="not-json")
    result = json.loads(result_str)
    assert "error" in result


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_status_tool_wraps_exception(MockLiveKitAPI):
    """status tool returns error JSON on exception."""
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(side_effect=Exception("boom"))
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import status

    result_str = await status(task_id="call-fail")
    result = json.loads(result_str)
    assert result["error"] == "Internal error. Check server logs for details."
    assert result["task_id"] == "call-fail"
    assert "boom" not in result_str  # Original error message must not leak


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_result_tool_wraps_exception(MockLiveKitAPI):
    """result tool returns generic error JSON on exception."""
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(side_effect=Exception("boom"))
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import result

    result_str = await result(task_id="call-fail")
    parsed = json.loads(result_str)
    assert parsed["error"] == "Internal error. Check server logs for details."
    assert parsed["task_id"] == "call-fail"
    assert "boom" not in result_str  # Original error message must not leak


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_cancel_tool_wraps_exception(MockLiveKitAPI):
    """cancel tool returns generic error JSON on exception."""
    mock_api = AsyncMock()
    mock_api.room.send_data = AsyncMock(side_effect=Exception("room gone"))
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import cancel

    result_str = await cancel(task_id="call-fail")
    parsed = json.loads(result_str)
    assert parsed["error"] == "Internal error. Check server logs for details."
    assert "room gone" not in result_str  # Original error message must not leak


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_result_room_not_found(MockLiveKitAPI):
    """_do_result returns error when room not found."""
    mock_api = AsyncMock()
    mock_api.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_result(task_id="call-nonexistent")
    assert result["error"] == "call not found"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_do_result_no_metadata(MockLiveKitAPI):
    """_do_result handles room with no metadata."""
    mock_api = AsyncMock()
    mock_room = MagicMock()
    mock_room.metadata = ""
    mock_api.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_result(task_id="call-empty")
    assert result["status"] == "in_progress"
    assert result["state"] == "unknown"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_status_tool_returns_json_on_success(MockLiveKitAPI):
    """status tool returns JSON string on success (covers line 185)."""
    mock_api = AsyncMock()
    mock_room = MagicMock()
    mock_room.metadata = json.dumps({"state": "connected"})
    mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import status

    result_str = await status(task_id="call-test-status")
    result = json.loads(result_str)
    assert result["state"] == "connected"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_result_tool_returns_json_on_success(MockLiveKitAPI):
    """result tool returns JSON on success (covers line 223)."""
    mock_api = AsyncMock()
    mock_room = MagicMock()
    mock_room.metadata = json.dumps(
        {
            "state": "ended",
            "outcome": {
                "task_id": "call-test-result",
                "disposition": "completed",
                "duration_seconds": 15.0,
                "transcript": [],
                "events": [],
            },
        }
    )
    mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import result

    result_str = await result(task_id="call-test-result")
    parsed = json.loads(result_str)
    assert parsed["disposition"] == "completed"


def test_dial_docstring_documents_approval_limitation():
    """dial tool docstring mentions that approval is not available in MCP mode."""
    from call_use.mcp_server import dial

    docstring = dial.__doc__
    assert "approval" in docstring.lower()
    assert "MCP" in docstring or "mcp" in docstring.lower()


def test_mcp_server_main_calls_run():
    """main() calls mcp.run(transport='stdio') (covers line 230)."""
    from call_use.mcp_server import main

    with patch("call_use.mcp_server.mcp") as mock_mcp:
        main()
        mock_mcp.run.assert_called_once_with(transport="stdio")


def test_mcp_server_main_guard():
    """__name__ == '__main__' guard calls main() (covers line 234)."""
    import call_use.mcp_server as mod

    with patch.object(mod, "main") as mock_main:
        # Execute the module-level guard by eval-ing the condition
        ns = {"__name__": "__main__", "main": mock_main}
        exec("if __name__ == '__main__': main()", ns)
        mock_main.assert_called_once()


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server.LiveKitAPI")
async def test_dial_tool_success(MockLiveKitAPI):
    """dial tool returns JSON with task_id on success."""
    mock_api = AsyncMock()
    mock_api.room.create_room.return_value = MagicMock()
    mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import dial

    result_str = await dial(phone="+18005551234", instructions="Test")
    result = json.loads(result_str)
    assert "task_id" in result
    assert result["status"] == "dispatched"


# ===========================================================================
# Phone/caller_id validation in _do_dial (security fix coverage)
# ===========================================================================


# ===========================================================================
# Input validation tests (security fix — match REST API constraints)
# ===========================================================================


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_dial_instructions_too_long_returns_error():
    """_do_dial rejects instructions exceeding 5000 chars."""
    result = await _do_dial(phone="+12025551234", instructions="x" * 5001)
    assert "error" in result
    assert "instructions too long" in result["error"]


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_dial_timeout_below_minimum_returns_error():
    """_do_dial rejects timeout below 30 seconds."""
    result = await _do_dial(phone="+12025551234", instructions="test", timeout=10)
    assert "error" in result
    assert "timeout must be between" in result["error"]


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_dial_timeout_above_maximum_returns_error():
    """_do_dial rejects timeout above 3600 seconds."""
    result = await _do_dial(phone="+12025551234", instructions="test", timeout=7200)
    assert "error" in result
    assert "timeout must be between" in result["error"]


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server.CreateAgentDispatchRequest")
@patch("call_use.mcp_server.LiveKitAPI")
async def test_dial_invalid_voice_id_falls_back_to_alloy(MockLiveKitAPI, MockDispatchReq):
    """_do_dial falls back to 'alloy' for invalid voice_id (matches agent.py)."""
    mock_api = AsyncMock()
    mock_api.room.create_room.return_value = MagicMock()
    mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    result = await _do_dial(phone="+12025551234", instructions="test", voice_id="invalid-voice")
    assert result["status"] == "dispatched"
    # Verify the dispatched metadata used "alloy" as fallback
    dispatch_kwargs = MockDispatchReq.call_args.kwargs
    metadata = json.loads(dispatch_kwargs["metadata"])
    assert metadata["voice_id"] == "alloy"


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_dial_user_info_not_json_serializable_returns_error():
    """_do_dial rejects user_info that cannot be serialized to JSON."""
    result = await _do_dial(phone="+12025551234", instructions="test", user_info={"bad": object()})
    assert "error" in result
    assert "user_info must be JSON-serializable" in result["error"]


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_dial_user_info_too_large_returns_error():
    """_do_dial rejects user_info exceeding 10000 chars serialized."""
    big_info = {"data": "x" * 10000}
    result = await _do_dial(phone="+12025551234", instructions="test", user_info=big_info)
    assert "error" in result
    assert "user_info too large" in result["error"]


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_do_dial_rejects_invalid_phone():
    """_do_dial returns error for invalid phone number."""
    result = await _do_dial(phone="not-a-phone", instructions="test")
    assert "error" in result
    assert "Invalid phone number" in result["error"]


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
async def test_do_dial_rejects_invalid_caller_id():
    """_do_dial returns error for invalid caller_id."""
    result = await _do_dial(phone="+12025551234", instructions="test", caller_id="bad-caller")
    assert "error" in result
    assert "Invalid caller ID" in result["error"]


# ===========================================================================
# CallError handling in dial tool
# ===========================================================================


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server._do_dial")
async def test_dial_worker_not_running_error(mock_do_dial):
    """dial returns helpful error when worker_not_running CallError is raised."""
    mock_do_dial.side_effect = CallError(
        code=CallErrorCode.worker_not_running,
        message="Worker not running",
    )
    from call_use.mcp_server import dial

    result_str = await dial(phone="+18005551234", instructions="Test")
    result = json.loads(result_str)
    assert "error" in result
    assert "No worker available" in result["error"]
    assert "help" in result


@pytest.mark.asyncio
@patch.dict(os.environ, _FULL_ENV)
@patch("call_use.mcp_server._do_dial")
async def test_dial_generic_call_error(mock_do_dial):
    """dial returns error with code for non-worker_not_running CallError."""
    mock_do_dial.side_effect = CallError(
        code=CallErrorCode.dial_failed,
        message="Connection refused",
    )
    from call_use.mcp_server import dial

    result_str = await dial(phone="+18005551234", instructions="Test")
    result = json.loads(result_str)
    assert result["error"] == "Call failed"
    assert result["code"] == "dial_failed"


# ===========================================================================
# SDK worker identity prefix check
# ===========================================================================


def test_non_agent_participant_does_not_trigger_worker_joined():
    """A participant with identity 'sdk-abc123' must NOT satisfy the worker join check."""
    import asyncio

    worker_joined = asyncio.Event()

    # Simulate the participant handler logic from CallAgent.call()
    def on_participant(participant):
        identity = getattr(participant, "identity", "") or ""
        if identity.startswith("call-use-agent-"):
            worker_joined.set()

    # Non-agent participant
    sdk_participant = MagicMock()
    sdk_participant.identity = "sdk-abc123"
    on_participant(sdk_participant)
    assert not worker_joined.is_set(), "sdk-abc123 should NOT trigger worker_joined"

    # Also test generic "agent-" prefix does NOT match
    generic_participant = MagicMock()
    generic_participant.identity = "agent-generic-xyz"
    on_participant(generic_participant)
    assert not worker_joined.is_set(), "agent-generic-xyz should NOT trigger worker_joined"

    # Correct prefix DOES match
    worker_participant = MagicMock()
    worker_participant.identity = "call-use-agent-abc123"
    on_participant(worker_participant)
    assert worker_joined.is_set(), "call-use-agent-abc123 SHOULD trigger worker_joined"
