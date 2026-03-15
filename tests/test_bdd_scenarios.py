"""BDD scenario tests for key user journeys not covered elsewhere.

Covers:
- MCP tool chaining (dial -> status -> result)
- REST API workflow (create -> get -> cancel)
- CLI error recovery paths
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# MCP Tool Chaining: dial -> status -> result
# ---------------------------------------------------------------------------

_FULL_ENV = {
    "LIVEKIT_URL": "wss://test",
    "LIVEKIT_API_KEY": "key",
    "LIVEKIT_API_SECRET": "secret",
    "SIP_TRUNK_ID": "trunk",
    "OPENAI_API_KEY": "sk-test",
}


@pytest.mark.bdd
class TestMCPToolChaining:
    """Scenario: User chains MCP tools to make a call and get results."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_dial_then_status_then_result(self, MockLiveKitAPI):
        """
        Given a user dials a phone number via MCP
        When they check status and then fetch the result
        Then they get the full call outcome
        """
        from call_use.mcp_server import _do_dial, _do_result, _do_status

        # -- Given: dial dispatches the call --
        mock_api = AsyncMock()
        mock_api.room.create_room.return_value = MagicMock()
        mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        dial_result = await _do_dial(phone="+18005551234", instructions="Ask about hours")
        assert dial_result["status"] == "dispatched"
        task_id = dial_result["task_id"]

        # -- When: status shows connected --
        mock_room_connected = MagicMock()
        mock_room_connected.metadata = json.dumps({"state": "connected"})
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room_connected])

        status_result = await _do_status(task_id=task_id)
        assert status_result["state"] == "connected"

        # -- Then: result shows completed outcome --
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
                        {"speaker": "callee", "text": "We're open 9 to 5."},
                    ],
                    "events": [],
                },
            }
        )
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room_ended])

        result = await _do_result(task_id=task_id)
        assert result["disposition"] == "completed"
        assert result["task_id"] == task_id
        assert len(result["transcript"]) == 2

    @pytest.mark.asyncio
    @patch.dict(os.environ, _FULL_ENV)
    @patch("call_use.mcp_server.LiveKitAPI")
    async def test_dial_then_status_in_progress_then_result(self, MockLiveKitAPI):
        """
        Given a user dials via MCP
        When they check result before the call ends
        Then they get in_progress status
        """
        from call_use.mcp_server import _do_dial, _do_result

        mock_api = AsyncMock()
        mock_api.room.create_room.return_value = MagicMock()
        mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
        MockLiveKitAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
        MockLiveKitAPI.return_value.__aexit__ = AsyncMock(return_value=False)

        dial_result = await _do_dial(phone="+18005551234", instructions="Test")
        task_id = dial_result["task_id"]

        # -- When: call is still in progress --
        mock_room = MagicMock()
        mock_room.metadata = json.dumps({"state": "connected"})
        mock_api.room.list_rooms.return_value = MagicMock(rooms=[mock_room])

        result = await _do_result(task_id=task_id)
        assert result["status"] == "in_progress"
        assert result["state"] == "connected"


# ---------------------------------------------------------------------------
# REST API Workflow: create -> get -> cancel
# ---------------------------------------------------------------------------


@pytest.mark.bdd
class TestRESTAPIWorkflow:
    """Scenario: User creates a call via REST, monitors it, then cancels."""

    @pytest.fixture
    def client_and_headers(self):
        from call_use.server import create_app

        api_key = "test-bdd-key"
        app = create_app(api_key=api_key)
        from fastapi.testclient import TestClient

        return TestClient(app), {"X-API-Key": api_key}

    def test_create_then_get_then_cancel(self, client_and_headers):
        """
        Given a user creates a call via POST /calls
        When they check its status via GET /calls/{id}
        And then cancel it via POST /calls/{id}/cancel
        Then they get appropriate responses at each step
        """
        client, headers = client_and_headers

        # -- Given: create a call --
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "fake-jwt"
        with patch.object(sys.modules["livekit"].api, "AccessToken", return_value=mock_token):
            resp = client.post(
                "/calls",
                json={"phone_number": "+12025551234", "instructions": "Test call"},
                headers=headers,
            )
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]
        assert task_id.startswith("call-")

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

        # -- Then: cancel the call --
        mock_room.metadata = json.dumps(
            {
                "agent_identity": "agent-test",
                "state": "connected",
            }
        )
        lkapi.room.send_data = AsyncMock()

        cancel_resp = client.post(f"/calls/{task_id}/cancel", headers=headers)
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelling"

    def test_create_with_bad_phone_then_retry(self, client_and_headers):
        """
        Given a user sends a bad phone number
        When they get a 400 error
        And retry with a valid phone number
        Then the second request succeeds
        """
        client, headers = client_and_headers

        # -- Given: bad phone number --
        resp = client.post(
            "/calls",
            json={"phone_number": "not-a-phone", "instructions": "Test"},
            headers=headers,
        )
        assert resp.status_code == 400

        # -- Then: retry with valid number --
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "fake-jwt"
        with patch.object(sys.modules["livekit"].api, "AccessToken", return_value=mock_token):
            resp = client.post(
                "/calls",
                json={"phone_number": "+12025551234", "instructions": "Test"},
                headers=headers,
            )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# CLI Error Recovery Paths
# ---------------------------------------------------------------------------


@pytest.mark.bdd
class TestCLIErrorRecovery:
    """Scenario: User encounters errors and recovers."""

    def test_bad_phone_then_good_phone(self):
        """
        Given a user dials with an invalid phone number
        When they get an error
        And retry with a valid phone number
        Then the second call succeeds
        """
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()

        # -- Given: bad phone --
        result = runner.invoke(main, ["dial", "bad-number", "-i", "test"])
        assert result.exit_code != 0

        # -- Then: good phone --
        with patch(
            "call_use.cli._run_call",
            return_value={
                "task_id": "t1",
                "disposition": "completed",
                "duration_seconds": 10,
                "transcript": [],
                "events": [],
            },
        ):
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
            assert result.exit_code == 0

    def test_connection_error_then_runtime_error(self):
        """
        Given a user gets a connection error
        When they retry and get a runtime error
        Then both errors show appropriate messages
        """
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()

        # -- Connection error --
        with patch("call_use.cli._run_call", side_effect=ConnectionError("refused")):
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
            assert result.exit_code == 1
            assert "Could not connect to LiveKit" in result.output

        # -- Runtime error --
        with patch("call_use.cli._run_call", side_effect=RuntimeError("server down")):
            result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
            assert result.exit_code == 1
            assert "server down" in result.output

    def test_invalid_json_user_info_recovery(self):
        """
        Given a user passes invalid JSON for --user-info
        When they get a parse error
        And retry with valid JSON
        Then the second call succeeds
        """
        from click.testing import CliRunner

        from call_use.cli import main

        runner = CliRunner()

        # -- Invalid JSON --
        result = runner.invoke(main, ["dial", "+18005551234", "-i", "test", "-u", "{bad"])
        assert result.exit_code == 2

        # -- Valid JSON --
        with patch(
            "call_use.cli._run_call",
            return_value={
                "task_id": "t1",
                "disposition": "completed",
                "duration_seconds": 10,
                "transcript": [],
                "events": [],
            },
        ):
            result = runner.invoke(
                main,
                ["dial", "+18005551234", "-i", "test", "-u", '{"name": "Alice"}'],
            )
            assert result.exit_code == 0
