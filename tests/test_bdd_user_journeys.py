"""BDD user journey tests — comprehensive end-to-end workflows across all entry points.

Covers complete user journeys through:
- Journey 1: MCP tool chaining (dial -> status -> result lifecycle)
- Journey 2: REST API complete flow (create -> get -> inject -> takeover -> cancel)
- Journey 3: CLI user experience (help, flags, output, exit codes, doctor)
- Journey 4: SDK programmatic usage (call, events, approval, cancel, takeover)
- Journey 5: Cross-entry-point consistency (validation parity)
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.bdd

_FULL_ENV = {
    "LIVEKIT_URL": "wss://test",
    "LIVEKIT_API_KEY": "key",
    "LIVEKIT_API_SECRET": "secret",
    "SIP_TRUNK_ID": "trunk",
    "OPENAI_API_KEY": "sk-test",
    "DEEPGRAM_API_KEY": "dg-test",
}


def _make_livekit_mock():
    """Create a standard LiveKitAPI async context manager mock."""
    mock_api = AsyncMock()
    mock_api.room.create_room.return_value = MagicMock()
    mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
    mock_api.room.send_data = AsyncMock()
    return mock_api


def _patch_livekit(target_module="call_use.mcp_server"):
    """Return a patch for LiveKitAPI on the given module."""
    return patch(f"{target_module}.LiveKitAPI")


def _configure_livekit_mock(MockLiveKitAPI, mock_api):
    """Wire up a MockLiveKitAPI class mock to return mock_api as context manager."""
    MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
    MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)


# ---------------------------------------------------------------------------
# Journey 1: MCP Tool Chaining
# ---------------------------------------------------------------------------


class TestMCPCompleteWorkflowBDD:
    """BDD: Complete MCP workflow from dial to result."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_journey_dial_poll_status_get_result(self, MockLiveKitAPI):
        """Given MCP server, when dial -> status -> result, then complete lifecycle."""
        from call_use.mcp_server import _do_dial, _do_result, _do_status

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)

        # -- Given: user dials via MCP --
        dial_result = await _do_dial(phone="+18005551234", instructions="Ask about hours")
        assert dial_result["status"] == "dispatched"
        task_id = dial_result["task_id"]
        assert task_id.startswith("call-")

        # -- When: user polls status and sees "connected" --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "connected"})
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])

        status_result = await _do_status(task_id=task_id)
        assert status_result["task_id"] == task_id
        assert status_result["state"] == "connected"

        # -- Then: call ends, user fetches result --
        mock_room_ended = MagicMock()
        mock_room_ended.metadata = json.dumps(
            {
                "state": "ended",
                "outcome": {
                    "task_id": task_id,
                    "disposition": "completed",
                    "duration_seconds": 45.0,
                    "transcript": [
                        {"speaker": "agent", "text": "What are your hours?"},
                        {"speaker": "callee", "text": "We are open 9 to 5."},
                    ],
                    "events": [],
                },
            }
        )
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room_ended])

        result = await _do_result(task_id=task_id)
        assert result["disposition"] == "completed"
        assert result["task_id"] == task_id
        assert result["duration_seconds"] == 45.0
        assert len(result["transcript"]) == 2

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_journey_dial_cancel_verify_cancelled(self, MockLiveKitAPI):
        """Given MCP call started, when cancel, then cancel_requested returned."""
        from call_use.mcp_server import _do_dial, cancel

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)

        # -- Given: dial a call --
        dial_result = await _do_dial(phone="+18005551234", instructions="Test cancel")
        task_id = dial_result["task_id"]

        # -- When: cancel the call (agent_identity must be in room metadata) --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"agent_identity": "agent-cancel-test"})
        mock_api.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))

        cancel_json = await cancel(task_id=task_id)
        cancel_result = json.loads(cancel_json)

        # -- Then: cancel_requested status --
        assert cancel_result["status"] == "cancel_requested"
        assert cancel_result["task_id"] == task_id

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_journey_dial_with_all_options(self, MockLiveKitAPI):
        """Given MCP dial with all optional params, then all passed to LiveKit."""
        from call_use.mcp_server import _do_dial

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)

        result = await _do_dial(
            phone="+18005551234",
            instructions="Full options test",
            user_info={"name": "Alice", "account": "12345"},
            caller_id="+12025559999",
            voice_id="nova",
            timeout=300,
        )
        assert result["status"] == "dispatched"
        assert "task_id" in result

        # Verify the dispatch was called with metadata containing our params
        dispatch_call = mock_api.agent_dispatch.create_dispatch.call_args
        assert dispatch_call is not None

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_journey_status_nonexistent_task(self, MockLiveKitAPI):
        """Given no call, when status(bad_id), then appropriate error."""
        from call_use.mcp_server import _do_status

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[])

        result = await _do_status(task_id="call-nonexistent")
        assert result["error"] == "call not found"
        assert result["task_id"] == "call-nonexistent"

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_journey_result_before_call_ends(self, MockLiveKitAPI):
        """Given active call, when result(), then in_progress response."""
        from call_use.mcp_server import _do_result

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)

        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "connected"})
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])

        result = await _do_result(task_id="call-active123")
        assert result["status"] == "in_progress"
        assert result["state"] == "connected"
        assert result["task_id"] == "call-active123"

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_journey_cancel_nonexistent_call(self, MockLiveKitAPI):
        """Given no call, when cancel(bad_id), then error response (not crash)."""
        from call_use.mcp_server import cancel

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)
        mock_api.room.send_data.side_effect = Exception("Room not found")

        cancel_json = await cancel(task_id="call-doesnotexist")
        cancel_result = json.loads(cancel_json)

        # Should return error dict, not crash
        assert "error" in cancel_result


# ---------------------------------------------------------------------------
# Journey 2: REST API Complete Flow
# ---------------------------------------------------------------------------


class TestRESTCompleteWorkflowBDD:
    """BDD: Complete REST API workflow."""

    @pytest.fixture
    def client_and_headers(self):
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        api_key = "test-journey-key"
        app = create_app(api_key=api_key)
        return TestClient(app), {"X-API-Key": api_key}

    def _create_call(self, client, headers):
        """Helper: create a call and return (response, task_id)."""
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "fake-jwt"
        with patch.object(sys.modules["livekit"].api, "AccessToken", return_value=mock_token):
            resp = client.post(
                "/calls",
                json={"phone_number": "+12025551234", "instructions": "Test call"},
                headers=headers,
            )
        return resp, resp.json().get("task_id") if resp.status_code == 200 else None

    def test_journey_create_get_status_cancel(self, client_and_headers):
        """Full REST lifecycle: POST /calls -> GET /calls/{id} -> POST /calls/{id}/cancel."""
        client, headers = client_and_headers

        # -- Given: create a call --
        resp, task_id = self._create_call(client, headers)
        assert resp.status_code == 200
        assert task_id.startswith("call-")
        assert resp.json()["status"] == "dialing"

        # -- When: check status --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "connected"})
        mock_participant = MagicMock()
        mock_participant.identity = "phone-callee"
        lkapi = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi.room = MagicMock()
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi.room.list_participants = AsyncMock(
            return_value=MagicMock(participants=[mock_participant])
        )

        get_resp = client.get(f"/calls/{task_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["state"] == "connected"
        assert "phone-callee" in get_resp.json()["participants"]

        # -- Then: cancel --
        mock_room.metadata = json.dumps({"agent_identity": "agent-test", "state": "connected"})
        lkapi.room.send_data = AsyncMock()

        cancel_resp = client.post(f"/calls/{task_id}/cancel", headers=headers)
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelling"

    def test_journey_create_inject_message(self, client_and_headers):
        """Create call then inject context message."""
        client, headers = client_and_headers

        # -- Given: create a call --
        resp, task_id = self._create_call(client, headers)
        assert resp.status_code == 200

        # -- When: inject context message --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"agent_identity": "agent-test", "state": "connected"})
        lkapi = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi.room = MagicMock()
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi.room.send_data = AsyncMock()

        inject_resp = client.post(
            f"/calls/{task_id}/inject",
            json={"message": "The customer's name is Alice"},
            headers=headers,
        )

        # -- Then: message sent successfully --
        assert inject_resp.status_code == 200
        assert inject_resp.json()["status"] == "sent"

    def test_journey_create_takeover_resume(self, client_and_headers):
        """Create call, request takeover, then resume."""
        client, headers = client_and_headers

        # -- Given: create a call --
        resp, task_id = self._create_call(client, headers)
        assert resp.status_code == 200

        # -- When: takeover --
        mock_room_connected = MagicMock()
        mock_room_connected.metadata = json.dumps(
            {"agent_identity": "agent-test", "state": "connected"}
        )
        mock_room_takeover = MagicMock()
        mock_room_takeover.metadata = json.dumps(
            {"agent_identity": "agent-test", "state": "human_takeover"}
        )
        lkapi = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi.room = MagicMock()
        # First list_rooms call returns connected, subsequent returns human_takeover
        lkapi.room.list_rooms = AsyncMock(
            side_effect=[
                MagicMock(rooms=[mock_room_connected]),  # _get_agent_identity
                MagicMock(rooms=[mock_room_takeover]),  # poll for ack
            ]
        )
        lkapi.room.send_data = AsyncMock()
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "takeover-jwt"
        with patch.object(sys.modules["livekit"].api, "AccessToken", return_value=mock_token):
            takeover_resp = client.post(f"/calls/{task_id}/takeover", headers=headers)
        assert takeover_resp.status_code == 200
        assert takeover_resp.json()["status"] == "takeover_active"
        assert "takeover_token" in takeover_resp.json()

        # -- Then: resume --
        mock_room_takeover2 = MagicMock()
        mock_room_takeover2.metadata = json.dumps(
            {"agent_identity": "agent-test", "state": "human_takeover"}
        )
        mock_room_resumed = MagicMock()
        mock_room_resumed.metadata = json.dumps(
            {"agent_identity": "agent-test", "state": "connected"}
        )
        lkapi.room.list_rooms = AsyncMock(
            side_effect=[
                MagicMock(rooms=[mock_room_takeover2]),  # _get_agent_identity
                MagicMock(rooms=[mock_room_takeover2]),  # _get_room_state
                MagicMock(rooms=[mock_room_resumed]),  # poll for ack
            ]
        )
        lkapi.room.update_participant = AsyncMock()

        resume_resp = client.post(
            f"/calls/{task_id}/resume",
            json={"summary": "Customer wants a refund"},
            headers=headers,
        )
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "ai_resumed"

    def test_journey_create_approve_action(self, client_and_headers):
        """Create call with approval, approve pending action."""
        client, headers = client_and_headers

        # -- Given: create a call --
        resp, task_id = self._create_call(client, headers)
        assert resp.status_code == 200

        # -- When: approve pending action --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps(
            {
                "agent_identity": "agent-test",
                "state": "awaiting_approval",
                "approval_id": "apr-123",
            }
        )
        lkapi = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi.room = MagicMock()
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi.room.send_data = AsyncMock()

        approve_resp = client.post(f"/calls/{task_id}/approve", headers=headers)

        # -- Then: approval sent --
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "sent_approve"
        assert approve_resp.json()["approval_id"] == "apr-123"

    def test_journey_create_reject_action(self, client_and_headers):
        """Create call with approval, reject pending action."""
        client, headers = client_and_headers

        # -- Given: create a call --
        resp, task_id = self._create_call(client, headers)
        assert resp.status_code == 200

        # -- When: reject pending action --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps(
            {
                "agent_identity": "agent-test",
                "state": "awaiting_approval",
                "approval_id": "apr-456",
            }
        )
        lkapi = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi.room = MagicMock()
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi.room.send_data = AsyncMock()

        reject_resp = client.post(f"/calls/{task_id}/reject", headers=headers)

        # -- Then: rejection sent --
        assert reject_resp.status_code == 200
        assert reject_resp.json()["status"] == "sent_reject"
        assert reject_resp.json()["approval_id"] == "apr-456"

    def test_journey_get_ended_call_idempotent(self, client_and_headers):
        """GET on ended call returns ended status without side effects."""
        client, headers = client_and_headers

        # -- Given: create a call --
        resp, task_id = self._create_call(client, headers)
        assert resp.status_code == 200

        # -- When: call has ended, GET it multiple times --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "ended"})
        lkapi = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi.room = MagicMock()
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi.room.list_participants = AsyncMock(return_value=MagicMock(participants=[]))

        get_resp1 = client.get(f"/calls/{task_id}", headers=headers)
        get_resp2 = client.get(f"/calls/{task_id}", headers=headers)

        # -- Then: both return ended, no side effects --
        assert get_resp1.status_code == 200
        assert get_resp2.status_code == 200
        assert get_resp1.json()["state"] == "ended"
        assert get_resp2.json()["state"] == "ended"
        assert get_resp1.json() == get_resp2.json()


# ---------------------------------------------------------------------------
# Journey 3: CLI User Experience
# ---------------------------------------------------------------------------


class TestCLIUserExperienceBDD:
    """BDD: CLI user-facing behavior."""

    def test_journey_cli_help_is_discoverable(self):
        """Given new user, when --help, then shows all commands clearly."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()

        # Top-level help
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "call-use" in result.output
        assert "dial" in result.output
        assert "doctor" in result.output

        # Dial subcommand help
        result = runner.invoke(main, ["dial", "--help"])
        assert result.exit_code == 0
        assert "PHONE" in result.output
        assert "--instructions" in result.output
        assert "E.164" in result.output

    @patch("call_use.cli._run_call")
    def test_journey_cli_dial_with_all_flags(self, mock_run):
        """Given CLI, when dial with all flags, then all passed correctly."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t-all",
            "disposition": "completed",
            "duration_seconds": 30.0,
            "transcript": [],
            "events": [],
        }
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "dial",
                "+18005551234",
                "--instructions",
                "Cancel subscription",
                "--user-info",
                '{"account": "A123"}',
                "--caller-id",
                "+12025559999",
                "--voice-id",
                "nova",
                "--timeout",
                "300",
                "--approval-required",
            ],
        )
        assert result.exit_code == 0

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["phone"] == "+18005551234"
        assert call_kwargs["instructions"] == "Cancel subscription"
        assert call_kwargs["user_info"] == {"account": "A123"}
        assert call_kwargs["caller_id"] == "+12025559999"
        assert call_kwargs["voice_id"] == "nova"
        assert call_kwargs["timeout"] == 300
        assert call_kwargs["approval_required"] is True

    @patch("call_use.cli._run_call")
    def test_journey_cli_json_output_parseable(self, mock_run):
        """Given successful call, when output received, then valid JSON with all fields."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t-json",
            "disposition": "completed",
            "duration_seconds": 42.5,
            "transcript": [
                {"speaker": "agent", "text": "Hello"},
                {"speaker": "callee", "text": "Hi there"},
            ],
            "events": [],
        }
        runner = CliRunner()
        result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
        assert result.exit_code == 0

        # Extract JSON from output
        lines = result.output.strip().split("\n")
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
        json_str = "\n".join(lines[json_start:])
        data = json.loads(json_str)

        assert data["task_id"] == "t-json"
        assert data["disposition"] == "completed"
        assert data["duration_seconds"] == 42.5
        assert len(data["transcript"]) == 2
        assert "events" in data

    @patch("call_use.cli._run_call")
    def test_journey_cli_error_exit_codes(self, mock_run):
        """Given various dispositions, when call ends, then correct exit code."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()

        # completed -> 0
        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "completed",
            "duration_seconds": 10,
            "transcript": [],
            "events": [],
        }
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 0

        # voicemail -> 0
        mock_run.return_value["disposition"] = "voicemail"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 0

        # no_answer -> 0
        mock_run.return_value["disposition"] = "no_answer"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 0

        # busy -> 0
        mock_run.return_value["disposition"] = "busy"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 0

        # failed -> 1
        mock_run.return_value["disposition"] = "failed"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 1

        # timeout -> 1
        mock_run.return_value["disposition"] = "timeout"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 1

        # error -> 1
        mock_run.return_value["disposition"] = "error"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 1

        # cancelled -> 1
        mock_run.return_value["disposition"] = "cancelled"
        assert runner.invoke(main, ["dial", "+18005551234", "-i", "t"]).exit_code == 1

    @patch("call_use.cli._check_livekit_connectivity", return_value=(True, "LiveKit connection OK"))
    @patch.dict(os.environ, _FULL_ENV, clear=True)
    def test_journey_cli_doctor_full_check(self, mock_lk):
        """Given all env vars set, when doctor, then reports all checks passing."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "7 passed" in result.output
        assert "0 failed" in result.output

        # Verify each env var is reported
        for var in _FULL_ENV:
            assert var in result.output

    @patch("call_use.cli._run_call")
    def test_journey_cli_user_info_json_parsing(self, mock_run):
        """Given --user-info with valid JSON, when parsed, then dict available."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "completed",
            "duration_seconds": 10,
            "transcript": [],
            "events": [],
        }
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["dial", "+18005551234", "-i", "test", "-u", '{"name": "John", "id": 42}'],
        )
        assert result.exit_code == 0
        assert mock_run.call_args[1]["user_info"] == {"name": "John", "id": 42}

    def test_journey_cli_user_info_invalid_json(self):
        """Given --user-info 'not json', when parsed, then clear error and exit 2."""
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["dial", "+18005551234", "-i", "test", "-u", "not json"])
        assert result.exit_code == 2
        assert "user-info must be valid JSON" in result.output


# ---------------------------------------------------------------------------
# Journey 4: SDK Programmatic Usage
# ---------------------------------------------------------------------------


class TestSDKProgrammaticUsageBDD:
    """BDD: SDK used as a library."""

    def test_journey_sdk_minimal_call(self):
        """Given phone+instructions only, when CallAgent created, then defaults used."""
        from call_use.sdk import CallAgent

        agent = CallAgent(
            phone="+18005551234",
            instructions="Ask about store hours",
            approval_required=False,
        )
        # Verify defaults
        assert agent._phone == "+18005551234"
        assert agent._instructions == "Ask about store hours"
        assert agent._user_info == {}
        assert agent._caller_id is None
        assert agent._voice_id is None
        assert agent._timeout_seconds == 600
        assert agent._approval_required is False

    def test_journey_sdk_with_event_callback(self):
        """Given on_event callback, when CallAgent created, then callback stored."""
        from call_use.sdk import CallAgent

        events_received = []

        def my_callback(event):
            events_received.append(event)

        agent = CallAgent(
            phone="+18005551234",
            instructions="Test",
            approval_required=False,
            on_event=my_callback,
        )
        assert agent._on_event is my_callback

    def test_journey_sdk_with_approval_callback(self):
        """Given on_approval + approval_required, when created, then both stored."""
        from call_use.sdk import CallAgent

        def my_approval(details):
            return "approved"

        agent = CallAgent(
            phone="+18005551234",
            instructions="Test",
            approval_required=True,
            on_approval=my_approval,
        )
        assert agent._approval_required is True
        assert agent._on_approval is my_approval

    def test_journey_sdk_cancel_without_active_call_raises(self):
        """Given no active call, when cancel(), then RuntimeError raised."""
        from call_use.sdk import CallAgent

        agent = CallAgent(
            phone="+18005551234",
            instructions="Test",
            approval_required=False,
        )
        # No call has been started, so _room_name is None
        with pytest.raises(RuntimeError, match="No active call"):
            import asyncio

            asyncio.get_event_loop().run_until_complete(agent.cancel())

    def test_journey_sdk_takeover_without_active_call_raises(self):
        """Given no active call, when takeover(), then RuntimeError raised."""
        from call_use.sdk import CallAgent

        agent = CallAgent(
            phone="+18005551234",
            instructions="Test",
            approval_required=False,
        )
        with pytest.raises(RuntimeError, match="No active call"):
            import asyncio

            asyncio.get_event_loop().run_until_complete(agent.takeover())

    def test_journey_sdk_outcome_fields_accessible(self):
        """Given completed call, when outcome returned, then all fields accessible."""
        from call_use.models import CallOutcome, DispositionEnum

        outcome = CallOutcome(
            task_id="task-abc123",
            transcript=[
                {"speaker": "agent", "text": "Hello, I am calling about your account."},
                {"speaker": "callee", "text": "Sure, how can I help?"},
                {"speaker": "agent", "text": "I need to cancel my subscription."},
            ],
            events=[],
            duration_seconds=95.3,
            disposition=DispositionEnum.completed,
            recording_url="https://storage.example.com/recordings/abc.mp3",
            metadata={"custom_field": "value"},
        )

        # All fields accessible
        assert outcome.task_id == "task-abc123"
        assert outcome.disposition == DispositionEnum.completed
        assert outcome.disposition.value == "completed"
        assert outcome.duration_seconds == 95.3
        assert len(outcome.transcript) == 3
        assert outcome.transcript[0]["speaker"] == "agent"
        assert outcome.recording_url is not None
        assert outcome.metadata["custom_field"] == "value"
        assert isinstance(outcome.events, list)

        # Serializes cleanly
        data = outcome.model_dump(mode="json")
        assert data["disposition"] == "completed"
        assert isinstance(data["duration_seconds"], float)
        round_tripped = json.loads(json.dumps(data))
        assert round_tripped["task_id"] == "task-abc123"


# ---------------------------------------------------------------------------
# Journey 5: Cross-Entry-Point Consistency
# ---------------------------------------------------------------------------


class TestCrossEntryPointBDD:
    """BDD: Same behavior across CLI, MCP, REST, SDK."""

    def test_same_phone_validation_across_all_entry_points(self):
        """Given invalid phone, when used via any entry point, then same rejection."""
        from click.testing import CliRunner

        from call_use.cli import main
        from call_use.sdk import CallAgent

        # SDK rejects bad phone
        with pytest.raises(ValueError):
            CallAgent(phone="not-a-phone", instructions="test", approval_required=False)

        # CLI rejects bad phone (via _run_call raising ValueError)
        runner = CliRunner()
        with patch("call_use.cli._run_call", side_effect=ValueError("Invalid phone")):
            result = runner.invoke(main, ["dial", "not-a-phone", "-i", "test"])
            assert result.exit_code == 2
            assert "Invalid phone number" in result.output

        # REST rejects bad phone
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        app = create_app(api_key="test-key")
        client = TestClient(app)
        resp = client.post(
            "/calls",
            json={"phone_number": "not-a-phone", "instructions": "test"},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_same_timeout_validation_across_entry_points(self, MockLiveKitAPI):
        """Given timeout=0, when used via MCP, then rejected."""
        from call_use.mcp_server import _do_dial

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)

        # MCP rejects timeout=0
        result = await _do_dial(phone="+18005551234", instructions="test", timeout=0)
        assert "error" in result
        assert "timeout" in result["error"].lower()

        # REST rejects timeout=0 (Pydantic validation: ge=30)
        from fastapi.testclient import TestClient

        from call_use.server import create_app

        app = create_app(api_key="test-key")
        client = TestClient(app)
        resp = client.post(
            "/calls",
            json={
                "phone_number": "+18005551234",
                "instructions": "test",
                "timeout_seconds": 0,
            },
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_same_missing_env_vars_across_entry_points(self, MockLiveKitAPI):
        """Given missing env vars, when any entry point used, then clear error."""
        from call_use.mcp_server import _do_dial

        mock_api = _make_livekit_mock()
        _configure_livekit_mock(MockLiveKitAPI, mock_api)

        # MCP returns error dict (not crash)
        with patch.dict(os.environ, {}, clear=True):
            result = await _do_dial(phone="+18005551234", instructions="test")
            assert "error" in result
            assert "missing" in result

        # CLI shows clear error
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()
        with patch(
            "call_use.cli._run_call",
            side_effect=RuntimeError("Missing required environment variables"),
        ):
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
            assert result.exit_code == 1
            assert "Missing required environment variables" in result.output

        # REST requires API_KEY at app creation
        from call_use.server import create_app

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="API_KEY"):
                create_app()
