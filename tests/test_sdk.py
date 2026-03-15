"""Tests for call_use.sdk — Step 10 CallAgent SDK class."""

# LiveKit mocks are set up in conftest.py (shared across all test files).

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.sdk import CallAgent


class TestCallAgentConstructor:
    def test_valid_inputs(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test task",
            on_approval=lambda d: "approved",
        )
        assert agent._phone == "+12025551234"
        assert agent._instructions == "Test task"

    def test_invalid_phone_raises(self):
        with pytest.raises(ValueError):
            CallAgent(
                phone="invalid",
                instructions="Test",
                on_approval=lambda d: "approved",
            )

    def test_invalid_caller_id_raises(self):
        with pytest.raises(ValueError):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                caller_id="bad-caller",
                on_approval=lambda d: "approved",
            )

    def test_approval_required_without_callback_raises(self):
        with pytest.raises(ValueError, match="on_approval"):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                approval_required=True,
                on_approval=None,
            )

    def test_approval_not_required_no_callback_ok(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        assert agent._approval_required is False

    def test_user_info_defaults_to_empty_dict(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            on_approval=lambda d: "approved",
        )
        assert agent._user_info == {}

    def test_empty_instructions_accepted(self):
        """Empty instructions are technically valid (agent uses defaults)."""
        agent = CallAgent(phone="+18002234567", instructions="", approval_required=False)
        assert agent._instructions == ""

    def test_very_long_instructions_accepted(self):
        """Long instructions should not crash."""
        long_text = "Do this. " * 1000
        agent = CallAgent(phone="+18002234567", instructions=long_text, approval_required=False)
        assert len(agent._instructions) > 5000

    def test_user_info_with_special_characters(self):
        """User info with unicode and special chars should work."""
        agent = CallAgent(
            phone="+18002234567",
            instructions="test",
            approval_required=False,
            user_info={"name": "José García", "notes": "账号 12345"},
        )
        assert agent._user_info["name"] == "José García"


class TestCallAgentCommands:
    async def test_send_command_raises_without_active_call(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            on_approval=lambda d: "approved",
        )
        with pytest.raises(RuntimeError, match="No active call"):
            await agent._send_command("takeover")

    async def test_cancel_raises_without_active_call(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        with pytest.raises(RuntimeError, match="No active call"):
            await agent.cancel()

    async def test_resume_raises_without_active_call(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        with pytest.raises(RuntimeError, match="No active call"):
            await agent.resume()

    async def test_takeover_raises_without_room_name(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        # _room_name is None, _send_command will raise first
        with pytest.raises(RuntimeError, match="No active call"):
            await agent.takeover()


class TestSendCommand:
    async def test_send_command_sends_data(self):
        """_send_command sends correct data to agent via LiveKitAPI."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        agent._room_name = "test-room-123"

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(
                rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')]
            )
        )
        mock_api.room.send_data = AsyncMock()

        with patch("call_use.sdk.LiveKitAPI") as MockLKAPI:
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)
            await agent._send_command("cancel")

        mock_api.room.send_data.assert_called_once()

    async def test_send_approval_response_approve(self):
        """_send_approval_response sends approve command."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(
                rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')]
            )
        )
        mock_api.room.send_data = AsyncMock()

        with patch("call_use.sdk.LiveKitAPI") as MockLKAPI:
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)
            await agent._send_approval_response("room-1", "apr-123", "approved")

        mock_api.room.send_data.assert_called_once()

    async def test_send_approval_response_reject(self):
        """_send_approval_response sends reject command when result is not 'approved'."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(
                rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')]
            )
        )
        mock_api.room.send_data = AsyncMock()

        with patch("call_use.sdk.LiveKitAPI") as MockLKAPI:
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)
            await agent._send_approval_response("room-1", "apr-123", "rejected")

        mock_api.room.send_data.assert_called_once()


class TestGetAgentIdentity:
    async def test_get_agent_identity_success(self):
        """_get_agent_identity returns agent identity from room metadata."""
        from call_use.sdk import _get_agent_identity

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(
                rooms=[MagicMock(metadata='{"agent_identity": "agent-xyz"}')]
            )
        )
        result = await _get_agent_identity(mock_api, "test-room")
        assert result == "agent-xyz"

    async def test_get_agent_identity_room_not_found(self):
        """_get_agent_identity raises RuntimeError when room not found."""
        from call_use.sdk import _get_agent_identity

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[])
        )
        with pytest.raises(RuntimeError, match="not found"):
            await _get_agent_identity(mock_api, "missing-room")

    async def test_get_agent_identity_no_agent_yet(self):
        """_get_agent_identity raises RuntimeError when agent not initialized."""
        from call_use.sdk import _get_agent_identity

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(
                rooms=[MagicMock(metadata='{"state": "created"}')]
            )
        )
        with pytest.raises(RuntimeError, match="not yet initialized"):
            await _get_agent_identity(mock_api, "test-room")


class TestCallAgentCallMethod:
    async def test_call_returns_outcome_on_complete(self):
        """call() returns CallOutcome when call_complete event is received."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            on_event=lambda e: None,
        )

        # Mock room
        mock_room = MagicMock()
        data_handler = None

        def capture_handler(event_name):
            def decorator(fn):
                nonlocal data_handler
                data_handler = fn
                return fn
            return decorator

        mock_room.on = capture_handler
        mock_room.connect = AsyncMock()
        mock_room.disconnect = AsyncMock()

        # Mock api
        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch.dict(os.environ, {
                "LIVEKIT_API_KEY": "test-key",
                "LIVEKIT_API_SECRET": "test-secret",
                "LIVEKIT_URL": "wss://test",
            }),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            # Simulate call_complete event after connect
            async def _simulate_complete():
                await asyncio.sleep(0.05)
                if data_handler:
                    dp = MagicMock()
                    dp.topic = "call-events"
                    dp.data = json.dumps({
                        "type": "call_complete",
                        "data": {
                            "task_id": "test-123",
                            "transcript": [],
                            "events": [],
                            "duration_seconds": 10.0,
                            "disposition": "completed",
                        },
                    }).encode()
                    data_handler(dp)

            task = asyncio.create_task(_simulate_complete())
            outcome = await agent.call()
            assert outcome.disposition == "completed"
            mock_room.disconnect.assert_called_once()

    async def test_call_timeout_returns_timeout_disposition(self):
        """call() returns timeout disposition when no complete event."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=0,  # Immediate timeout
        )

        mock_room = MagicMock()
        mock_room.on = lambda event_name: (lambda fn: fn)
        mock_room.connect = AsyncMock()
        mock_room.disconnect = AsyncMock()

        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()
        # Fallback room listing returns no rooms
        mock_lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch.dict(os.environ, {
                "LIVEKIT_API_KEY": "test-key",
                "LIVEKIT_API_SECRET": "test-secret",
                "LIVEKIT_URL": "wss://test",
            }),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            outcome = await agent.call()
            assert outcome.disposition == "timeout"

    async def test_takeover_returns_jwt(self):
        """takeover() returns a JWT token for human to join."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        agent._room_name = "test-room"

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(
                rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')]
            )
        )
        mock_api.room.send_data = AsyncMock()

        with (
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch.dict(os.environ, {
                "LIVEKIT_API_KEY": "test-key",
                "LIVEKIT_API_SECRET": "test-secret",
            }),
        ):
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)
            MockToken.return_value.to_jwt.return_value = "human-jwt-token"

            jwt = await agent.takeover()
            assert jwt == "human-jwt-token"
