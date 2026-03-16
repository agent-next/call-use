"""Tests for call_use.sdk — Step 10 CallAgent SDK class."""

# LiveKit mocks are set up in conftest.py (shared across all test files).

import asyncio
import json
import os
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from call_use.sdk import CallAgent

pytestmark = pytest.mark.unit


async def _selective_timeout(coro, timeout):
    """Only raise TimeoutError for the call timeout (>= 60s), not other wait_for calls."""
    if timeout >= 60:  # call timeout = timeout_seconds + 30, minimum 60
        await asyncio.sleep(0.1)  # let background tasks run before raising
        raise asyncio.TimeoutError()
    return await asyncio.wait_for(coro, timeout)


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

    def test_timeout_too_low_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be between 30 and 3600"):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                approval_required=False,
                timeout_seconds=0,
            )

    def test_timeout_too_high_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be between 30 and 3600"):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                approval_required=False,
                timeout_seconds=7200,
            )

    def test_timeout_negative_raises(self):
        with pytest.raises(ValueError, match="timeout_seconds must be between 30 and 3600"):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                approval_required=False,
                timeout_seconds=-1,
            )

    def test_timeout_at_bounds_accepted(self):
        agent_low = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
            timeout_seconds=30,
        )
        assert agent_low._timeout_seconds == 30
        agent_high = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
            timeout_seconds=3600,
        )
        assert agent_high._timeout_seconds == 3600

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
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
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
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
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
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
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
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-xyz"}')])
        )
        result = await _get_agent_identity(mock_api, "test-room")
        assert result == "agent-xyz"

    async def test_get_agent_identity_room_not_found(self):
        """_get_agent_identity raises RuntimeError when room not found."""
        from call_use.sdk import _get_agent_identity

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))
        with pytest.raises(RuntimeError, match="not found"):
            await _get_agent_identity(mock_api, "missing-room")

    async def test_get_agent_identity_no_agent_yet(self):
        """_get_agent_identity raises RuntimeError when agent not initialized."""
        from call_use.sdk import _get_agent_identity

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[MagicMock(metadata='{"state": "created"}')])
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
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
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
                    dp.data = json.dumps(
                        {
                            "type": "call_complete",
                            "data": {
                                "task_id": "test-123",
                                "transcript": [],
                                "events": [],
                                "duration_seconds": 10.0,
                                "disposition": "completed",
                            },
                        }
                    ).encode()
                    data_handler(dp)

            asyncio.create_task(_simulate_complete())
            outcome = await agent.call()
            assert outcome.disposition == "completed"
            mock_room.disconnect.assert_called_once()

    async def test_call_timeout_returns_timeout_disposition(self):
        """call() returns timeout disposition when no complete event."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=30,
        )

        mock_room = MagicMock()
        mock_room.on = lambda event_name: lambda fn: fn
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
            patch("call_use.sdk.asyncio.wait_for", side_effect=_selective_timeout),
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            outcome = await agent.call()
            assert outcome.disposition == "timeout"

    async def test_call_ignores_non_call_events_topic(self):
        """call() data handler ignores packets with non-call-events topic (line 107)."""
        events_received = []

        def on_event(e):
            events_received.append(e)

        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            on_event=on_event,
            timeout_seconds=30,
        )

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

        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()
        mock_lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.asyncio.wait_for", side_effect=_selective_timeout),
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            # Send a non-call-events packet before call times out
            async def _send_other_topic():
                await asyncio.sleep(0.05)
                if data_handler:
                    dp = MagicMock()
                    dp.topic = "other-topic"
                    dp.data = json.dumps(
                        {"type": "transcript", "data": {"speaker": "agent", "text": "Hi"}}
                    ).encode()
                    data_handler(dp)

            asyncio.create_task(_send_other_topic())
            outcome = await agent.call()
            assert outcome.disposition == "timeout"
            # The non-call-events packet should have been ignored — no events fired
            assert len(events_received) == 0

    async def test_call_on_event_callback_fires(self):
        """call() invokes on_event callback when data is received (covers line 107)."""
        events_received = []

        def on_event(e):
            events_received.append(e)

        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            on_event=on_event,
        )

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

        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            async def _simulate_events():
                await asyncio.sleep(0.05)
                if data_handler:
                    # First: a transcript event (non-complete, fires on_event)
                    dp = MagicMock()
                    dp.topic = "call-events"
                    dp.data = json.dumps(
                        {
                            "type": "transcript",
                            "data": {"speaker": "agent", "text": "Hi"},
                        }
                    ).encode()
                    data_handler(dp)
                    await asyncio.sleep(0.05)
                    # Then: call_complete
                    dp2 = MagicMock()
                    dp2.topic = "call-events"
                    dp2.data = json.dumps(
                        {
                            "type": "call_complete",
                            "data": {
                                "task_id": "test-ev",
                                "transcript": [],
                                "events": [],
                                "duration_seconds": 5.0,
                                "disposition": "completed",
                            },
                        }
                    ).encode()
                    data_handler(dp2)

            asyncio.create_task(_simulate_events())
            outcome = await agent.call()
            assert outcome.disposition == "completed"
            # Give the executor time to fire the callback
            await asyncio.sleep(0.1)
            assert len(events_received) > 0

    async def test_call_approval_request_handler(self):
        """call() handles approval_request events via on_approval callback (lines 120-131)."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=True,
            on_approval=lambda data: "approved",
        )

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

        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()
        # Mock for _send_approval_response
        mock_lkapi.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
        )
        mock_lkapi.room.send_data = AsyncMock()

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            async def _simulate_approval_then_complete():
                await asyncio.sleep(0.05)
                if data_handler:
                    # Send approval request
                    dp = MagicMock()
                    dp.topic = "call-events"
                    dp.data = json.dumps(
                        {
                            "type": "approval_request",
                            "data": {
                                "approval_id": "apr-test",
                                "details": "Refund $50",
                            },
                        }
                    ).encode()
                    data_handler(dp)
                    await asyncio.sleep(0.2)  # Give time for approval handling
                    # Then complete
                    dp2 = MagicMock()
                    dp2.topic = "call-events"
                    dp2.data = json.dumps(
                        {
                            "type": "call_complete",
                            "data": {
                                "task_id": "test-apr",
                                "transcript": [],
                                "events": [],
                                "duration_seconds": 10.0,
                                "disposition": "completed",
                            },
                        }
                    ).encode()
                    data_handler(dp2)

            asyncio.create_task(_simulate_approval_then_complete())
            outcome = await agent.call()
            assert outcome.disposition == "completed"

    async def test_call_reads_outcome_from_metadata_fallback(self):
        """call() reads outcome from room metadata when no call_complete event (lines 175-179)."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=30,
        )

        mock_room = MagicMock()
        mock_room.on = lambda event_name: lambda fn: fn
        mock_room.connect = AsyncMock()
        mock_room.disconnect = AsyncMock()

        # Metadata fallback returns outcome
        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()
        mock_fallback_room = MagicMock()
        mock_fallback_room.metadata = json.dumps(
            {
                "state": "ended",
                "outcome": {
                    "task_id": "test-fallback",
                    "transcript": [],
                    "events": [],
                    "duration_seconds": 20.0,
                    "disposition": "completed",
                },
            }
        )
        mock_lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_fallback_room]))

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.asyncio.wait_for", side_effect=_selective_timeout),
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            outcome = await agent.call()
            assert outcome.disposition == "completed"
            assert outcome.task_id == "test-fallback"

    async def test_call_metadata_fallback_exception_handled(self):
        """call() handles exception when reading metadata fallback (lines 178-179)."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=30,
        )

        mock_room = MagicMock()
        mock_room.on = lambda event_name: lambda fn: fn
        mock_room.connect = AsyncMock()
        mock_room.disconnect = AsyncMock()

        # First LiveKitAPI context is for dispatch (succeeds)
        # Second LiveKitAPI context is for fallback metadata read (fails)
        dispatch_api = AsyncMock()
        dispatch_api.agent_dispatch.create_dispatch = AsyncMock()

        fallback_api = AsyncMock()
        fallback_api.room.list_rooms = AsyncMock(side_effect=Exception("network error"))

        enter_count = [0]

        async def mock_aenter(*args):
            enter_count[0] += 1
            if enter_count[0] == 1:
                return dispatch_api
            return fallback_api

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.asyncio.wait_for", side_effect=_selective_timeout),
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = mock_aenter
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            outcome = await agent.call()
            assert outcome.disposition == "timeout"

    async def test_takeover_raises_without_room_name_after_send(self):
        """takeover() raises RuntimeError when _room_name is None after _send_command (line 198)."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        # Set _room_name for _send_command but then clear it
        agent._room_name = "temp-room"

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
        )
        mock_api.room.send_data = AsyncMock()

        with patch("call_use.sdk.LiveKitAPI") as MockLKAPI:
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            # Patch _send_command to succeed but then clear room_name
            original_send = agent._send_command

            async def patched_send(cmd):
                await original_send(cmd)
                agent._room_name = None

            agent._send_command = patched_send

            with (
                patch("call_use.sdk.api.AccessToken") as MockToken,
                patch.dict(
                    os.environ,
                    {
                        "LIVEKIT_API_KEY": "test-key",
                        "LIVEKIT_API_SECRET": "test-secret",
                    },
                ),
            ):
                MockToken.return_value.to_jwt.return_value = "jwt"
                import pytest as pt

                with pt.raises(RuntimeError, match="room name unavailable"):
                    await agent.takeover()

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
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
        )
        mock_api.room.send_data = AsyncMock()

        with (
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                },
            ),
        ):
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)
            MockToken.return_value.to_jwt.return_value = "human-jwt-token"

            jwt = await agent.takeover()
            assert jwt == "human-jwt-token"


class TestTokenTTL:
    """Verify that SDK tokens are created with explicit TTL values."""

    async def test_call_monitor_token_has_2h_ttl(self):
        """call() creates a monitor token with 2-hour TTL."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=30,
        )

        mock_room = MagicMock()
        mock_room.on = lambda event_name: lambda fn: fn
        mock_room.connect = AsyncMock()
        mock_room.disconnect = AsyncMock()

        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()
        mock_lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                },
            ),
        ):
            mock_token_instance = MockToken.return_value
            mock_token_instance.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            await agent.call()

            mock_token_instance.with_ttl.assert_called_once_with(timedelta(hours=2))

    async def test_takeover_token_has_15min_ttl(self):
        """takeover() creates a human token with 15-minute TTL."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        agent._room_name = "test-room"

        mock_api = AsyncMock()
        mock_api.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[MagicMock(metadata='{"agent_identity": "agent-abc"}')])
        )
        mock_api.room.send_data = AsyncMock()

        with (
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                },
            ),
        ):
            mock_token_instance = MockToken.return_value
            mock_token_instance.to_jwt.return_value = "human-jwt-token"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            await agent.takeover()

            mock_token_instance.with_ttl.assert_called_once_with(timedelta(minutes=15))
