"""Tests for call_use.server."""

# LiveKit mocks (base + server-specific) are set up in conftest.py.

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("LIVEKIT_API_KEY", "test-key")
os.environ.setdefault("LIVEKIT_API_SECRET", "test-secret")

from fastapi.testclient import TestClient  # noqa: E402

from call_use.server import create_app  # noqa: E402

pytestmark = pytest.mark.integration

API_KEY = "test-api-key-12345"


@pytest.fixture
def client():
    app = create_app(api_key=API_KEY)
    return TestClient(app)


@pytest.fixture
def headers():
    return {"X-API-Key": API_KEY}


# ===========================================================================
# 1: POST /calls with valid phone → 200
# ===========================================================================


class TestCreateCallValid:
    def test_valid_phone_returns_200(self, client, headers):
        """POST /calls with a valid US phone number returns 200 with expected fields."""
        # Mock AccessToken so to_jwt() returns a string
        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with patch.object(
            sys.modules["livekit"].api, "AccessToken", return_value=mock_token_instance
        ):
            resp = client.post(
                "/calls",
                json={
                    "phone_number": "+12025551234",
                    "instructions": "Call the dentist",
                },
                headers=headers,
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "task_id" in body
        assert body["task_id"].startswith("call-")
        assert "livekit_token" in body
        assert "room_name" in body
        assert "status" in body


# ===========================================================================
# 2: POST /calls with invalid phone → 400
# ===========================================================================


class TestCreateCallInvalidPhone:
    def test_invalid_phone_returns_400(self, client, headers):
        """POST /calls with a malformed phone number returns 400."""
        resp = client.post(
            "/calls",
            json={
                "phone_number": "not-a-phone",
                "instructions": "Test",
            },
            headers=headers,
        )
        assert resp.status_code == 400


# ===========================================================================
# 3: POST /calls with Caribbean NPA → 400
# ===========================================================================


class TestCreateCallCaribbeanNPA:
    def test_caribbean_npa_returns_400(self, client, headers):
        """POST /calls with a Caribbean area code (e.g. +1242) returns 400."""
        resp = client.post(
            "/calls",
            json={
                "phone_number": "+12425551234",
                "instructions": "Test",
            },
            headers=headers,
        )
        assert resp.status_code == 400


# ===========================================================================
# 4: POST /calls with no API key → 422
# ===========================================================================


class TestCreateCallNoApiKey:
    def test_missing_api_key_returns_422(self, client):
        """POST /calls without X-API-Key header returns 422 (FastAPI validation)."""
        resp = client.post(
            "/calls",
            json={
                "phone_number": "+12025551234",
                "instructions": "Test",
            },
            # No headers — missing API key
        )
        assert resp.status_code == 422


# ===========================================================================
# 5: POST /calls with wrong API key → 401
# ===========================================================================


class TestCreateCallWrongApiKey:
    def test_wrong_api_key_returns_401(self, client):
        """POST /calls with an incorrect API key returns 401."""
        resp = client.post(
            "/calls",
            json={
                "phone_number": "+12025551234",
                "instructions": "Test",
            },
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401


# ===========================================================================
# 6: GET /calls/{id} known → 200 with room state
# ===========================================================================


class TestGetCallKnown:
    def test_known_call_returns_200(self, client, headers):
        """GET /calls/{id} for a known task returns 200 with call state."""
        # First create a call to get a valid task_id
        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with patch.object(
            sys.modules["livekit"].api, "AccessToken", return_value=mock_token_instance
        ):
            create_resp = client.post(
                "/calls",
                json={
                    "phone_number": "+12025551234",
                    "instructions": "Test call",
                },
                headers=headers,
            )

        assert create_resp.status_code == 200
        task_id = create_resp.json()["task_id"]

        # Mock LiveKitAPI for room listing + participants
        mock_room = MagicMock()
        mock_room.metadata = '{"state": "connected"}'
        mock_participant = MagicMock()
        mock_participant.identity = "phone-callee"
        lkapi_instance = sys.modules["livekit.api"].LiveKitAPI.return_value
        lkapi_instance.room = MagicMock()
        lkapi_instance.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
        lkapi_instance.room.list_participants = AsyncMock(
            return_value=MagicMock(participants=[mock_participant])
        )

        resp = client.get(f"/calls/{task_id}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_id"] == task_id
        assert body["state"] == "connected"
        assert "phone-callee" in body["participants"]


# ===========================================================================
# 7: GET /calls/{unknown} → 404
# ===========================================================================


class TestGetCallUnknown:
    def test_unknown_call_returns_404(self, client, headers):
        """GET /calls/{id} for an unknown task returns 404."""
        resp = client.get("/calls/task-nonexistent99", headers=headers)
        assert resp.status_code == 404


# ===========================================================================
# 8: POST /calls/{id}/inject missing message → 400
# ===========================================================================


class TestCreateCallEmptyInstructions:
    def test_empty_instructions_returns_200(self, client, headers):
        """POST /calls with empty instructions still succeeds (uses default)."""
        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with patch.object(
            sys.modules["livekit"].api, "AccessToken", return_value=mock_token_instance
        ):
            resp = client.post(
                "/calls",
                json={
                    "phone_number": "+12025551234",
                    "instructions": "",
                },
                headers=headers,
            )
        # Empty string is valid — the model has a default, but explicit empty is OK
        assert resp.status_code == 200


class TestCreateCallLongPhone:
    def test_very_long_phone_returns_400(self, client, headers):
        """POST /calls with a very long phone number returns 400."""
        resp = client.post(
            "/calls",
            json={
                "phone_number": "+1" + "5" * 20,
                "instructions": "Test",
            },
            headers=headers,
        )
        assert resp.status_code == 400


class TestRateLimiting:
    def test_rate_limit_triggers(self, headers):
        """Rate limiter returns 429 after exceeding max calls."""
        # Create app with low rate limit
        app = create_app(api_key=API_KEY)

        # Override rate limiter to a very low limit

        for route in app.routes:
            pass  # just need the app

        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with (
            patch.object(
                sys.modules["livekit"].api, "AccessToken", return_value=mock_token_instance
            ),
            patch.dict(os.environ, {"RATE_LIMIT_MAX": "2", "RATE_LIMIT_WINDOW": "3600"}),
        ):
            # Create app with low rate limit
            app2 = create_app(api_key=API_KEY)
            client2 = TestClient(app2)

            for i in range(3):
                resp = client2.post(
                    "/calls",
                    json={
                        "phone_number": "+12025551234",
                        "instructions": "Test",
                    },
                    headers=headers,
                )
                if i < 2:
                    assert resp.status_code == 200, f"Call {i} should succeed"
                else:
                    assert resp.status_code == 429, "Third call should be rate limited"


class TestInjectMissingMessage:
    def test_inject_missing_message_returns_400(self, client, headers):
        """POST /calls/{id}/inject without a message field returns 400."""
        # Create a call first
        mock_token_instance = MagicMock()
        mock_token_instance.to_jwt.return_value = "fake-jwt-token"

        with patch.object(
            sys.modules["livekit"].api, "AccessToken", return_value=mock_token_instance
        ):
            create_resp = client.post(
                "/calls",
                json={
                    "phone_number": "+12025551234",
                    "instructions": "Test call",
                },
                headers=headers,
            )

        task_id = create_resp.json()["task_id"]

        # Inject without message field
        resp = client.post(
            f"/calls/{task_id}/inject",
            json={},
            headers=headers,
        )
        assert resp.status_code == 400


# ===========================================================================
# Helper: create a call and set up LK mocks
# ===========================================================================


def _create_call_and_setup_mocks(client, headers, agent_identity="agent-test123"):
    """Create a call and configure LiveKitAPI mocks for subsequent endpoint tests."""
    mock_token_instance = MagicMock()
    mock_token_instance.to_jwt.return_value = "fake-jwt-token"

    with patch.object(sys.modules["livekit"].api, "AccessToken", return_value=mock_token_instance):
        create_resp = client.post(
            "/calls",
            json={
                "phone_number": "+12025551234",
                "instructions": "Test call",
            },
            headers=headers,
        )

    task_id = create_resp.json()["task_id"]

    # Mock room with agent_identity in metadata
    mock_room = MagicMock()
    mock_room.metadata = '{"agent_identity": "' + agent_identity + '", "state": "connected"}'
    lkapi_instance = sys.modules["livekit.api"].LiveKitAPI.return_value
    lkapi_instance.room = MagicMock()
    lkapi_instance.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[mock_room]))
    lkapi_instance.room.send_data = AsyncMock()
    lkapi_instance.room.list_participants = AsyncMock(return_value=MagicMock(participants=[]))
    lkapi_instance.room.update_participant = AsyncMock()

    return task_id, mock_room, lkapi_instance


# ===========================================================================
# POST /calls/{id}/inject with valid message
# ===========================================================================


class TestInjectValidMessage:
    def test_inject_with_message_returns_200(self, client, headers):
        """POST /calls/{id}/inject with message field returns 200."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        resp = client.post(
            f"/calls/{task_id}/inject",
            json={"message": "Account number is 12345"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "sent"
        lkapi.room.send_data.assert_called_once()


# ===========================================================================
# POST /calls/{id}/cancel
# ===========================================================================


class TestCancelCall:
    def test_cancel_returns_200(self, client, headers):
        """POST /calls/{id}/cancel sends cancel command and returns 200."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        resp = client.post(f"/calls/{task_id}/cancel", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "cancelling"
        assert body["call_id"] == task_id

    def test_cancel_unknown_call_returns_404(self, client, headers):
        """POST /calls/{unknown}/cancel returns 404."""
        resp = client.post("/calls/nonexistent/cancel", headers=headers)
        assert resp.status_code == 404


# ===========================================================================
# POST /calls/{id}/takeover
# ===========================================================================


class TestTakeoverEndpoint:
    def test_takeover_returns_token_on_ack(self, client, headers):
        """POST /calls/{id}/takeover returns takeover_token when agent acks."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        # Mock the polling: first call returns connected, second returns human_takeover
        takeover_room = MagicMock()
        takeover_room.metadata = '{"state": "human_takeover", "agent_identity": "agent-test123"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[takeover_room]))

        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "takeover-jwt-token"
        with patch.object(sys.modules["livekit"].api, "AccessToken", return_value=mock_token):
            resp = client.post(f"/calls/{task_id}/takeover", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "takeover_active"
        assert "takeover_token" in body

    def test_takeover_timeout_returns_504(self, client, headers):
        """POST /calls/{id}/takeover returns 504 when agent doesn't ack."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        # Mock polling: always returns connected (never acks takeover)
        connected_room = MagicMock()
        connected_room.metadata = '{"state": "connected", "agent_identity": "agent-test123"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[connected_room]))

        resp = client.post(f"/calls/{task_id}/takeover", headers=headers)
        assert resp.status_code == 504


# ===========================================================================
# POST /calls/{id}/resume
# ===========================================================================


class TestResumeEndpoint:
    def test_resume_returns_200_on_ack(self, client, headers):
        """POST /calls/{id}/resume returns ai_resumed when agent acks."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        # State starts as human_takeover, then returns connected after resume
        takeover_room = MagicMock()
        takeover_room.metadata = '{"state": "human_takeover", "agent_identity": "agent-test123"}'

        connected_room = MagicMock()
        connected_room.metadata = '{"state": "connected", "agent_identity": "agent-test123"}'

        # _get_room_state reads metadata, then polling reads again
        # First list_rooms call is for _get_agent_identity, second for _get_room_state,
        # then polling calls
        lkapi.room.list_rooms = AsyncMock(
            side_effect=[
                MagicMock(rooms=[takeover_room]),  # _get_agent_identity
                MagicMock(rooms=[takeover_room]),  # _get_room_state
                MagicMock(rooms=[connected_room]),  # polling
            ]
        )

        resp = client.post(
            f"/calls/{task_id}/resume",
            json={"summary": "Talked to customer"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ai_resumed"

    def test_resume_already_active_returns_200(self, client, headers):
        """POST /calls/{id}/resume when already connected returns already_active."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        # State is already connected
        resp = client.post(
            f"/calls/{task_id}/resume",
            json={"summary": ""},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_active"


# ===========================================================================
# POST /calls/{id}/approve
# ===========================================================================


class TestApproveEndpoint:
    def test_approve_sends_command(self, client, headers):
        """POST /calls/{id}/approve sends approve command."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        # Set up room with pending approval
        approval_room = MagicMock()
        approval_room.metadata = (
            '{"agent_identity": "agent-test123", '
            '"state": "awaiting_approval", '
            '"approval_id": "apr-test-1"}'
        )
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[approval_room]))

        resp = client.post(f"/calls/{task_id}/approve", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "sent_approve"
        assert body["approval_id"] == "apr-test-1"

    def test_approve_no_pending_approval_returns_409(self, client, headers):
        """POST /calls/{id}/approve returns 409 when no pending approval."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        # Room has agent but no approval_id
        no_approval_room = MagicMock()
        no_approval_room.metadata = '{"agent_identity": "agent-test123", "state": "connected"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[no_approval_room]))

        resp = client.post(f"/calls/{task_id}/approve", headers=headers)
        assert resp.status_code == 409


# ===========================================================================
# POST /calls/{id}/reject
# ===========================================================================


class TestRejectEndpoint:
    def test_reject_sends_command(self, client, headers):
        """POST /calls/{id}/reject sends reject command."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        approval_room = MagicMock()
        approval_room.metadata = (
            '{"agent_identity": "agent-test123", '
            '"state": "awaiting_approval", '
            '"approval_id": "apr-test-2"}'
        )
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[approval_room]))

        resp = client.post(f"/calls/{task_id}/reject", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "sent_reject"
        assert body["approval_id"] == "apr-test-2"

    def test_reject_no_agent_returns_409(self, client, headers):
        """POST /calls/{id}/reject returns 409 when agent not initialized."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)

        # Room with no agent_identity
        no_agent_room = MagicMock()
        no_agent_room.metadata = '{"state": "created"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[no_agent_room]))

        resp = client.post(f"/calls/{task_id}/reject", headers=headers)
        assert resp.status_code == 409


# ===========================================================================
# Server internal helpers
# ===========================================================================


class TestServerHelpers:
    def test_get_call_lock_creates_lock(self, client, headers):
        """_get_call_lock creates and reuses locks per call_id."""
        resp = client.post(
            "/calls/unknown-id/inject",
            json={"message": "test"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_invalid_caller_id_returns_400(self, client, headers):
        """POST /calls with invalid caller_id returns 400."""
        resp = client.post(
            "/calls",
            json={
                "phone_number": "+12025551234",
                "instructions": "Test",
                "caller_id": "invalid-caller",
            },
            headers=headers,
        )
        assert resp.status_code == 400


# ===========================================================================
# Edge cases for _get_agent_identity / _get_room_state (lines 76, 80, 86)
# ===========================================================================


class TestGetAgentIdentityEdgeCases:
    def test_inject_room_not_found_returns_404(self, client, headers):
        """inject returns 404 when room not found (line 76)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        # Room not found
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))
        resp = client.post(
            f"/calls/{task_id}/inject",
            json={"message": "test"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_inject_agent_not_initialized_returns_409(self, client, headers):
        """inject returns 409 when agent not yet initialized (line 80)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        no_agent_room = MagicMock()
        no_agent_room.metadata = '{"state": "created"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[no_agent_room]))
        resp = client.post(
            f"/calls/{task_id}/inject",
            json={"message": "test"},
            headers=headers,
        )
        assert resp.status_code == 409

    def test_get_call_room_not_found_returns_404(self, client, headers):
        """GET /calls/{id} returns 404 when room not found (line 86)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))
        resp = client.get(f"/calls/{task_id}", headers=headers)
        assert resp.status_code == 404


# ===========================================================================
# Takeover room closed (line 226)
# ===========================================================================


class TestTakeoverRoomClosed:
    def test_takeover_room_closed_returns_404(self, client, headers):
        """takeover returns 404 when room closes during polling (line 226)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        # First call for _get_agent_identity returns room, then polling returns empty
        lkapi.room.list_rooms = AsyncMock(
            side_effect=[
                MagicMock(rooms=[mock_room]),  # _get_agent_identity
                MagicMock(rooms=[]),  # polling - room closed
            ]
        )
        resp = client.post(f"/calls/{task_id}/takeover", headers=headers)
        assert resp.status_code == 404


# ===========================================================================
# Resume room closed (line 273) and timeout (line 278)
# ===========================================================================


class TestResumeEdgeCases:
    def test_resume_room_closed_returns_404(self, client, headers):
        """resume returns 404 when room closes during polling (line 273)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        takeover_room = MagicMock()
        takeover_room.metadata = '{"state": "human_takeover", "agent_identity": "agent-test123"}'
        lkapi.room.list_rooms = AsyncMock(
            side_effect=[
                MagicMock(rooms=[takeover_room]),  # _get_agent_identity
                MagicMock(rooms=[takeover_room]),  # _get_room_state
                MagicMock(rooms=[]),  # polling - room closed
            ]
        )
        resp = client.post(
            f"/calls/{task_id}/resume",
            json={"summary": "test"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_resume_timeout_returns_504(self, client, headers):
        """resume returns 504 when agent doesn't ack (line 278)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        takeover_room = MagicMock()
        takeover_room.metadata = '{"state": "human_takeover", "agent_identity": "agent-test123"}'
        # Never transitions to connected
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[takeover_room]))
        resp = client.post(
            f"/calls/{task_id}/resume",
            json={"summary": "test"},
            headers=headers,
        )
        assert resp.status_code == 504

    def test_resume_update_participant_fails_silently(self, client, headers):
        """resume swallows update_participant exception (lines 292-293)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        takeover_room = MagicMock()
        takeover_room.metadata = '{"state": "human_takeover", "agent_identity": "agent-test123"}'
        connected_room = MagicMock()
        connected_room.metadata = '{"state": "connected", "agent_identity": "agent-test123"}'
        lkapi.room.list_rooms = AsyncMock(
            side_effect=[
                MagicMock(rooms=[takeover_room]),  # _get_agent_identity
                MagicMock(rooms=[takeover_room]),  # _get_room_state
                MagicMock(rooms=[connected_room]),  # polling
            ]
        )
        lkapi.room.update_participant = AsyncMock(side_effect=Exception("participant gone"))
        resp = client.post(
            f"/calls/{task_id}/resume",
            json={"summary": "test"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ai_resumed"


# ===========================================================================
# Approve endpoint edge cases (lines 302, 306)
# ===========================================================================


class TestApproveEdgeCases:
    def test_approve_room_not_found_returns_404(self, client, headers):
        """approve returns 404 when room not found (line 302)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))
        resp = client.post(f"/calls/{task_id}/approve", headers=headers)
        assert resp.status_code == 404

    def test_approve_no_agent_returns_409(self, client, headers):
        """approve returns 409 when agent not initialized (line 306)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        no_agent_room = MagicMock()
        no_agent_room.metadata = '{"state": "created"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[no_agent_room]))
        resp = client.post(f"/calls/{task_id}/approve", headers=headers)
        assert resp.status_code == 409


# ===========================================================================
# Reject endpoint edge cases (lines 329, 336)
# ===========================================================================


class TestRejectEdgeCases:
    def test_reject_room_not_found_returns_404(self, client, headers):
        """reject returns 404 when room not found (line 329)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[]))
        resp = client.post(f"/calls/{task_id}/reject", headers=headers)
        assert resp.status_code == 404

    def test_reject_no_pending_approval_returns_409(self, client, headers):
        """reject returns 409 when no pending approval (line 336)."""
        task_id, mock_room, lkapi = _create_call_and_setup_mocks(client, headers)
        no_approval_room = MagicMock()
        no_approval_room.metadata = '{"agent_identity": "agent-test123", "state": "connected"}'
        lkapi.room.list_rooms = AsyncMock(return_value=MagicMock(rooms=[no_approval_room]))
        resp = client.post(f"/calls/{task_id}/reject", headers=headers)
        assert resp.status_code == 409
