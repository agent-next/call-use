"""Tests for call-use MCP server tools."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.mcp_server import _do_dial, _do_result, _do_status


@pytest.mark.asyncio
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
    mock_room.metadata = json.dumps({
        "state": "ended",
        "outcome": {
            "task_id": "call-test-123",
            "disposition": "completed",
            "duration_seconds": 30.0,
            "transcript": [{"speaker": "agent", "text": "Hello"}],
            "events": [],
        },
    })
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
