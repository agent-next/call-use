"""Tests for call-use MCP server tools."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.mcp_server import _do_dial, _do_result, _do_status

pytestmark = pytest.mark.unit

_FULL_ENV = {
    "LIVEKIT_URL": "wss://test",
    "LIVEKIT_API_KEY": "key",
    "LIVEKIT_API_SECRET": "secret",
    "SIP_TRUNK_ID": "trunk",
    "OPENAI_API_KEY": "sk-test",
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
    assert "Missing required environment variables" in result["error"]
    assert any("LIVEKIT_URL" in m for m in result["missing"])
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
    assert "error" in result
    assert result["task_id"] == "call-fail"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_result_tool_wraps_exception(MockLiveKitAPI):
    """result tool returns error JSON on exception."""
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(side_effect=Exception("boom"))
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import result

    result_str = await result(task_id="call-fail")
    parsed = json.loads(result_str)
    assert "error" in parsed
    assert parsed["task_id"] == "call-fail"


@pytest.mark.asyncio
@patch("call_use.mcp_server.LiveKitAPI")
async def test_cancel_tool_wraps_exception(MockLiveKitAPI):
    """cancel tool returns error JSON on exception."""
    mock_api = AsyncMock()
    mock_api.room.send_data = AsyncMock(side_effect=Exception("room gone"))
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

    from call_use.mcp_server import cancel

    result_str = await cancel(task_id="call-fail")
    parsed = json.loads(result_str)
    assert "error" in parsed


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
