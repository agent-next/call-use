"""Tests for call_use.server — Step 6."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock livekit modules before importing server
for mod in [
    "livekit", "livekit.api", "livekit.protocol", "livekit.protocol.models",
    "dotenv",
]:
    sys.modules.setdefault(mod, MagicMock())

# We need to mock LiveKitAPI as an async context manager
mock_livekit_api = MagicMock()
mock_lkapi_instance = MagicMock()
mock_lkapi_instance.__aenter__ = AsyncMock(return_value=mock_lkapi_instance)
mock_lkapi_instance.__aexit__ = AsyncMock(return_value=None)
mock_livekit_api.return_value = mock_lkapi_instance

# Mock agent_dispatch.create_dispatch
mock_lkapi_instance.agent_dispatch = MagicMock()
mock_lkapi_instance.agent_dispatch.create_dispatch = AsyncMock()

# Set LiveKitAPI in livekit.api module
sys.modules["livekit.api"].LiveKitAPI = mock_livekit_api

# Mock api module attributes needed
lk_api_mod = sys.modules["livekit"].api
lk_api_mod.AccessToken = MagicMock
lk_api_mod.VideoGrants = MagicMock
lk_api_mod.CreateAgentDispatchRequest = MagicMock
lk_api_mod.ListRoomsRequest = MagicMock
lk_api_mod.ListParticipantsRequest = MagicMock
lk_api_mod.SendDataRequest = MagicMock
lk_api_mod.UpdateRoomMetadataRequest = MagicMock

import os
os.environ.setdefault("LIVEKIT_API_KEY", "test-key")
os.environ.setdefault("LIVEKIT_API_SECRET", "test-secret")

from call_use.server import create_app
from fastapi.testclient import TestClient

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
        mock_lkapi_instance.room = MagicMock()
        mock_lkapi_instance.room.list_rooms = AsyncMock(
            return_value=MagicMock(rooms=[mock_room])
        )
        mock_lkapi_instance.room.list_participants = AsyncMock(
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
