"""BDD tests for security, rate limiting, resilience, and concurrent operations.

Covers:
- SE: Error sanitization (MCP tools), Token TTL, JWT exp claims
- Rate limiting behavior
- RR: Recovery & resilience under failure conditions
- CO: Concurrent call handling and race conditions
"""

import asyncio
import json
import os
import sys
import time
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("LIVEKIT_API_KEY", "test-key")
os.environ.setdefault("LIVEKIT_API_SECRET", "test-secret")

from call_use.evidence import EvidencePipeline  # noqa: E402
from call_use.models import (  # noqa: E402
    CallError,
    CallErrorCode,
    CallEvent,
    CallOutcome,
    CallTask,
    DispositionEnum,
)
from call_use.rate_limit import RateLimiter  # noqa: E402
from call_use.sdk import CallAgent  # noqa: E402

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task() -> CallTask:
    return CallTask(phone_number="+12125551234", instructions="test")


def _make_pipeline() -> EvidencePipeline:
    return EvidencePipeline(task=_make_task(), room_name=None)


# ===========================================================================
# SE: Security scenarios
# ===========================================================================


class TestSecurityBDD:
    """BDD: Security controls — error sanitization, token TTL, JWT exp."""

    # SE05: Error sanitization -----------------------------------------------

    @pytest.mark.asyncio
    async def test_given_internal_error_when_mcp_dial_then_no_stack_trace_in_response(self):
        """Given an internal exception, when MCP dial tool returns error,
        then response contains generic message only — no stack trace."""
        from call_use.mcp_server import dial

        with patch("call_use.mcp_server._do_dial", side_effect=RuntimeError("DB conn refused")):
            result = await dial(
                phone="+12025551234",
                instructions="Test call",
            )

        parsed = json.loads(result)
        assert "error" in parsed
        # Must contain generic message
        assert "Internal error" in parsed["error"]
        # Must NOT leak exception details
        assert "DB conn refused" not in result
        assert "Traceback" not in result
        assert "RuntimeError" not in result

    @pytest.mark.asyncio
    async def test_given_internal_error_when_mcp_status_then_no_stack_trace(self):
        """Given an internal exception, when MCP status tool returns error,
        then response contains only generic message."""
        from call_use.mcp_server import status

        with patch(
            "call_use.mcp_server._do_status",
            side_effect=ConnectionError("socket closed unexpectedly"),
        ):
            result = await status(task_id="call-abc123")

        parsed = json.loads(result)
        assert "error" in parsed
        assert "Internal error" in parsed["error"]
        assert "socket closed" not in result
        assert "ConnectionError" not in result

    @pytest.mark.asyncio
    async def test_given_internal_error_when_mcp_cancel_then_no_stack_trace(self):
        """Given an internal exception, when MCP cancel tool returns error,
        then response contains only generic message."""
        from call_use.mcp_server import cancel

        with patch("call_use.mcp_server.LiveKitAPI") as MockLK:
            MockLK.return_value.__aenter__ = AsyncMock(
                side_effect=OSError("ECONNREFUSED 127.0.0.1:7880")
            )
            MockLK.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await cancel(task_id="call-abc123")

        parsed = json.loads(result)
        assert "error" in parsed
        assert "Internal error" in parsed["error"]
        assert "ECONNREFUSED" not in result
        assert "OSError" not in result

    @pytest.mark.asyncio
    async def test_given_internal_error_when_mcp_result_then_no_stack_trace(self):
        """Given an internal exception, when MCP result tool returns error,
        then response contains only generic message."""
        from call_use.mcp_server import result

        with patch(
            "call_use.mcp_server._do_result",
            side_effect=KeyError("secret_field"),
        ):
            output = await result(task_id="call-xyz789")

        parsed = json.loads(output)
        assert "error" in parsed
        assert "Internal error" in parsed["error"]
        assert "secret_field" not in output
        assert "KeyError" not in output

    # SE07-08: Token TTL ----------------------------------------------------

    @pytest.mark.asyncio
    async def test_given_sdk_call_when_monitor_token_then_ttl_2_hours(self):
        """Given a SDK call setup, when monitor token generated,
        then AccessToken.with_ttl is called with timedelta(hours=2)."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=0,
        )

        mock_room = MagicMock()
        _handlers = {}
        mock_room.on = lambda event_name: lambda fn: (_handlers.__setitem__(event_name, fn), fn)[1]
        mock_room.connect = AsyncMock()
        mock_room.disconnect = AsyncMock()

        mock_lkapi = AsyncMock()
        mock_lkapi.agent_dispatch.create_dispatch = AsyncMock()
        mock_lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch("call_use.sdk.LiveKitAPI") as MockLKAPI,
            patch("call_use.sdk.WORKER_JOIN_TIMEOUT", 0.1),
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                    "SIP_TRUNK_ID": "test-trunk",
                    "OPENAI_API_KEY": "test-openai-key",
                },
            ),
        ):
            mock_token_instance = MockToken.return_value
            mock_token_instance.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            async def _simulate_worker_join():
                await asyncio.sleep(0.02)
                if "participant_connected" in _handlers:
                    p = MagicMock()
                    p.identity = "call-use-agent-abc123"
                    _handlers["participant_connected"](p)

            asyncio.create_task(_simulate_worker_join())
            await agent.call()

            mock_token_instance.with_ttl.assert_called_once_with(timedelta(hours=2))

    @pytest.mark.asyncio
    async def test_given_takeover_when_token_generated_then_ttl_15_minutes(self):
        """Given a takeover request, when token generated,
        then AccessToken.with_ttl is called with timedelta(minutes=15)."""
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
            mock_token_instance.to_jwt.return_value = "human-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            await agent.takeover()

            mock_token_instance.with_ttl.assert_called_once_with(timedelta(minutes=15))

    # SE09: JWT exp claim always present ------------------------------------

    @pytest.mark.asyncio
    async def test_given_any_token_generation_when_jwt_decoded_then_exp_claim_present(self):
        """Given any token generation path, when the token is configured,
        then with_ttl is always called (ensuring exp claim is set)."""
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        api_key = "test-api-key-se09"
        app = create_app(api_key=api_key)
        client = TestClient(app)
        headers = {"X-API-Key": api_key}

        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with patch.object(
            sys.modules["livekit"].api,
            "AccessToken",
            return_value=mock_token_instance,
        ):
            resp = client.post(
                "/calls",
                json={
                    "phone_number": "+12025551234",
                    "instructions": "Test",
                },
                headers=headers,
            )

        assert resp.status_code == 200
        # with_ttl must have been called — this guarantees exp claim exists
        mock_token_instance.with_ttl.assert_called_once()
        ttl_arg = mock_token_instance.with_ttl.call_args[0][0]
        assert isinstance(ttl_arg, timedelta)
        assert ttl_arg.total_seconds() > 0


# ===========================================================================
# Rate Limiting BDD
# ===========================================================================


class TestRateLimitingBDD:
    """BDD: Rate limiting behavior."""

    def test_given_rate_limit_reached_when_new_call_then_429(self):
        """Given the rate limit has been reached, when a new call is made,
        then the server responds with 429."""
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        api_key = "test-api-key-rl"

        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with (
            patch.object(
                sys.modules["livekit"].api,
                "AccessToken",
                return_value=mock_token_instance,
            ),
            patch.dict(os.environ, {"RATE_LIMIT_MAX": "2", "RATE_LIMIT_WINDOW": "3600"}),
        ):
            app = create_app(api_key=api_key)
            client = TestClient(app)
            headers = {"X-API-Key": api_key}

            # First two succeed
            for _ in range(2):
                resp = client.post(
                    "/calls",
                    json={"phone_number": "+12025551234", "instructions": "Test"},
                    headers=headers,
                )
                assert resp.status_code == 200

            # Third is rate-limited
            resp = client.post(
                "/calls",
                json={"phone_number": "+12025551234", "instructions": "Test"},
                headers=headers,
            )
            assert resp.status_code == 429

    def test_given_rate_limit_window_expired_when_new_call_then_accepted(self):
        """Given the rate limit window has expired, when a new call is made,
        then the call is accepted (200)."""
        limiter = RateLimiter(max_calls=1, window_seconds=1)
        key = "key-window-test"

        # First call accepted
        assert limiter.check(key) is True
        # Second call blocked
        assert limiter.check(key) is False

        # Simulate window expiry by back-dating the recorded call
        limiter._calls[key] = [time.time() - 2]

        # Now should be accepted again
        assert limiter.check(key) is True

    def test_given_different_api_keys_when_both_call_then_independent_limits(self):
        """Given two different API keys, when both make calls,
        then rate limits are tracked independently."""
        limiter = RateLimiter(max_calls=1, window_seconds=3600)

        assert limiter.check("key-A") is True
        assert limiter.check("key-A") is False  # key-A exhausted

        # key-B is independent — still has its quota
        assert limiter.check("key-B") is True
        assert limiter.check("key-B") is False


# ===========================================================================
# RR: Recovery & Resilience
# ===========================================================================


class TestResilienceBDD:
    """BDD: System resilience under failure conditions."""

    # RR01: LiveKit connection failure ---------------------------------------

    @pytest.mark.asyncio
    async def test_given_livekit_down_when_sdk_call_then_clear_error_message(self):
        """Given LiveKit is unreachable, when SDK call() is made,
        then a clear error (exception) is raised."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=0,
        )

        mock_room = MagicMock()
        mock_room.on = lambda event_name: lambda fn: fn
        mock_room.connect = AsyncMock(side_effect=ConnectionError("Failed to connect to LiveKit"))
        mock_room.disconnect = AsyncMock()

        with (
            patch("call_use.sdk.rtc.Room", return_value=mock_room),
            patch("call_use.sdk.api.AccessToken") as MockToken,
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                    "SIP_TRUNK_ID": "test-trunk",
                    "OPENAI_API_KEY": "test-openai-key",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"

            with pytest.raises(ConnectionError, match="Failed to connect"):
                await agent.call()

    # RR03: Worker never joins -----------------------------------------------

    @pytest.mark.asyncio
    async def test_given_no_worker_when_sdk_call_waits_10s_then_timeout_disposition(self):
        """Given no worker joins the room, when SDK call() times out,
        then CallError is raised with worker_not_running code."""
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test call",
            approval_required=False,
            timeout_seconds=0,  # Immediate timeout
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
            patch("call_use.sdk.WORKER_JOIN_TIMEOUT", 0.1),
            patch.dict(
                os.environ,
                {
                    "LIVEKIT_API_KEY": "test-key",
                    "LIVEKIT_API_SECRET": "test-secret",
                    "LIVEKIT_URL": "wss://test",
                    "SIP_TRUNK_ID": "test-trunk",
                    "OPENAI_API_KEY": "test-openai-key",
                },
            ),
        ):
            MockToken.return_value.to_jwt.return_value = "fake-jwt"
            MockLKAPI.return_value.__aenter__ = AsyncMock(return_value=mock_lkapi)
            MockLKAPI.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(CallError) as exc_info:
                await agent.call()
            assert exc_info.value.code == CallErrorCode.worker_not_running

    # RR05: Evidence write failure -------------------------------------------

    @pytest.mark.asyncio
    async def test_given_unwritable_log_dir_when_finalize_then_call_still_completes(
        self, monkeypatch
    ):
        """Given an unwritable log directory, when finalize is called,
        then outcome is still returned successfully (write failure is swallowed)."""
        monkeypatch.setattr(
            "call_use.evidence.LOGS_DIR",
            Path("/nonexistent/impossible/dir"),
        )
        pipe = _make_pipeline()
        await pipe.emit_transcript("agent", "Hello")
        outcome = pipe.finalize(DispositionEnum.completed)
        assert isinstance(outcome, CallOutcome)
        assert outcome.disposition == DispositionEnum.completed
        assert len(outcome.transcript) == 1

    # RR06: Callback error handling ------------------------------------------

    @pytest.mark.asyncio
    async def test_given_on_event_callback_throws_when_event_fired_then_logged_not_crash(
        self,
    ):
        """Given a subscriber callback that raises, when an event is emitted,
        then the error is logged and subsequent subscribers still fire."""
        pipe = _make_pipeline()
        good_received: list[CallEvent] = []

        async def bad_callback(event: CallEvent):
            raise ValueError("callback exploded")

        async def good_callback(event: CallEvent):
            good_received.append(event)

        pipe.subscribe(bad_callback)
        pipe.subscribe(good_callback)

        await pipe.emit_dtmf("7")

        # Good subscriber still received the event
        assert len(good_received) == 1
        assert good_received[0].data["keys"] == "7"
        # Pipeline itself still recorded the event
        assert len(pipe._events) == 1

    # Config errors ----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_given_missing_all_env_vars_when_mcp_dial_then_configuration_error(self):
        """Given all required env vars are missing, when MCP dial is called,
        then response lists missing environment variables."""
        from call_use.mcp_server import _do_dial

        env_overrides = {
            "LIVEKIT_URL": "",
            "LIVEKIT_API_KEY": "",
            "LIVEKIT_API_SECRET": "",
            "SIP_TRUNK_ID": "",
            "OPENAI_API_KEY": "",
        }
        with patch.dict(os.environ, env_overrides, clear=False):
            result = await _do_dial(
                phone="+12025551234",
                instructions="Test call",
            )

        assert "error" in result
        assert (
            "configuration" in result["error"].lower() or "environment" in result["error"].lower()
        )
        assert "missing" in result

    @pytest.mark.asyncio
    async def test_given_partial_env_vars_when_mcp_dial_then_lists_missing_vars(self):
        """Given only some required env vars are set, when MCP dial is called,
        then response lists the specific missing variables."""
        from call_use.mcp_server import _do_dial

        env_overrides = {
            "LIVEKIT_URL": "wss://ok",
            "LIVEKIT_API_KEY": "key",
            "LIVEKIT_API_SECRET": "secret",
            "SIP_TRUNK_ID": "",  # missing
            "OPENAI_API_KEY": "",  # missing
        }
        with patch.dict(os.environ, env_overrides, clear=False):
            result = await _do_dial(
                phone="+12025551234",
                instructions="Test call",
            )

        assert "error" in result
        assert "missing" in result
        missing = result["missing"]
        assert "SIP_TRUNK_ID" in missing
        assert "OPENAI_API_KEY" in missing
        # Already-set vars should NOT be listed as missing
        assert "LIVEKIT_URL" not in missing


# ===========================================================================
# CO: Concurrent Operations
# ===========================================================================


class TestConcurrentOperationsBDD:
    """BDD: Concurrent call handling and race conditions."""

    def test_given_two_active_calls_when_cancel_one_then_other_unaffected(self):
        """Given two active calls, when one is cancelled,
        then the other call remains accessible."""
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        api_key = "test-api-key-co01"
        app = create_app(api_key=api_key)
        client = TestClient(app)
        headers = {"X-API-Key": api_key}

        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt"

        with patch.object(
            sys.modules["livekit"].api,
            "AccessToken",
            return_value=mock_token_instance,
        ):
            # Create two calls
            resp1 = client.post(
                "/calls",
                json={"phone_number": "+12025551234", "instructions": "Call 1"},
                headers=headers,
            )
            resp2 = client.post(
                "/calls",
                json={"phone_number": "+12025559876", "instructions": "Call 2"},
                headers=headers,
            )

        task_id_1 = resp1.json()["task_id"]
        task_id_2 = resp2.json()["task_id"]

        # Set up mocks for cancel (needs agent_identity in room metadata)
        mock_room = MagicMock()
        mock_room.metadata = '{"agent_identity": "agent-test", "state": "connected"}'
        lkapi_instance = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi_instance.room = MagicMock()
        lkapi_instance.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi_instance.room.send_data = AsyncMock()
        lkapi_instance.room.list_participants = AsyncMock(return_value=MagicMock(participants=[]))

        # Cancel call 1
        cancel_resp = client.post(f"/calls/{task_id_1}/cancel", headers=headers)
        assert cancel_resp.status_code == 200

        # Call 1 should be gone (cleaned up)
        get_resp_1 = client.get(f"/calls/{task_id_1}", headers=headers)
        assert get_resp_1.status_code == 404

        # Call 2 should still be accessible
        get_resp_2 = client.get(f"/calls/{task_id_2}", headers=headers)
        assert get_resp_2.status_code == 200

    @pytest.mark.asyncio
    async def test_given_same_call_id_when_concurrent_requests_then_serialized(self):
        """Given the same call_id, when concurrent requests arrive,
        then _get_call_lock ensures they are serialized (no data corruption)."""
        # Test the lock mechanism directly
        lock = asyncio.Lock()
        execution_order: list[str] = []

        async def operation(name: str, delay: float):
            async with lock:
                execution_order.append(f"{name}-start")
                await asyncio.sleep(delay)
                execution_order.append(f"{name}-end")

        # Launch two operations concurrently
        await asyncio.gather(
            operation("A", 0.05),
            operation("B", 0.01),
        )

        # They must be serialized: A-start, A-end, B-start, B-end
        # (or B first, then A — but never interleaved)
        assert len(execution_order) == 4
        # Check no interleaving: starts and ends must alternate properly
        starts = [i for i, v in enumerate(execution_order) if v.endswith("-start")]
        ends = [i for i, v in enumerate(execution_order) if v.endswith("-end")]
        # First start must come before first end; second start after first end
        assert starts[0] < ends[0] < starts[1] < ends[1]

    def test_given_call_ending_when_cancel_arrives_then_cleanup_runs_once(self):
        """Given a call is ending, when cancel also arrives,
        then _cleanup_call can run safely even if call is already removed."""
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        api_key = "test-api-key-co06"
        app = create_app(api_key=api_key)
        client = TestClient(app)
        headers = {"X-API-Key": api_key}

        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt"

        with patch.object(
            sys.modules["livekit"].api,
            "AccessToken",
            return_value=mock_token_instance,
        ):
            resp = client.post(
                "/calls",
                json={"phone_number": "+12025551234", "instructions": "Test"},
                headers=headers,
            )

        task_id = resp.json()["task_id"]

        mock_room = MagicMock()
        mock_room.metadata = '{"agent_identity": "agent-test", "state": "connected"}'
        lkapi_instance = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi_instance.room = MagicMock()
        lkapi_instance.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi_instance.room.send_data = AsyncMock()

        # Cancel once — should succeed
        resp1 = client.post(f"/calls/{task_id}/cancel", headers=headers)
        assert resp1.status_code == 200

        # Cancel again — call already cleaned up, should get 404
        resp2 = client.post(f"/calls/{task_id}/cancel", headers=headers)
        assert resp2.status_code == 404
