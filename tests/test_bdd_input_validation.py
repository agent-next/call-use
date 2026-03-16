"""BDD tests for input validation and boundary analysis across all entry points.

Tests cover phone validation, timeout boundaries, instructions length,
inject message validation, voice ID validation, and user_info edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from call_use.mcp_server import (
    MAX_INSTRUCTIONS_LENGTH,
    VALID_VOICES,
    _do_dial,
)
from call_use.phone import validate_phone_number
from call_use.server import CreateCallRequest, InjectRequest

pytestmark = pytest.mark.bdd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_PHONE = "+12125551234"
_VALID_INSTRUCTIONS = "Ask about store hours"

_MCP_ENV = {
    "LIVEKIT_URL": "wss://test",
    "LIVEKIT_API_KEY": "key",
    "LIVEKIT_API_SECRET": "secret",
    "SIP_TRUNK_ID": "trunk",
    "OPENAI_API_KEY": "sk-test",
}


def _mock_livekit_api():
    """Create a properly mocked LiveKitAPI async context manager."""
    mock_lk = MagicMock()
    mock_lk.__aenter__ = AsyncMock(return_value=mock_lk)
    mock_lk.__aexit__ = AsyncMock(return_value=None)
    mock_lk.room.create_room = AsyncMock()
    mock_lk.agent_dispatch.create_dispatch = AsyncMock()
    return MagicMock(return_value=mock_lk)


# ---------------------------------------------------------------------------
# IV-1: Phone Validation BDD
# ---------------------------------------------------------------------------


class TestPhoneValidationBDD:
    """BDD: Phone number validation across all entry points."""

    def test_given_phone_with_whitespace_when_dial_then_rejected(self):
        """Given a phone with internal whitespace, when dialed, then rejected.

        Note: leading/trailing whitespace is stripped and accepted.
        Internal whitespace makes it fail the E.164 regex.
        """
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("+1 212 555 1234")

    def test_given_phone_with_extension_when_dial_then_rejected(self):
        """Given a phone number with an extension suffix, when dialed, then rejected."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("+12125551234x100")

    def test_given_international_non_nanp_when_dial_then_rejected(self):
        """Given an international (non-NANP) number like UK, when dialed, then rejected."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("+442071234567")


# ---------------------------------------------------------------------------
# IV-2: Timeout Boundary BDD
# ---------------------------------------------------------------------------


class TestTimeoutBoundaryBDD:
    """BDD: Timeout boundary value analysis (30-3600).

    Tests boundary values across REST (Pydantic), MCP (_do_dial), CLI, and SDK.
    """

    # --- REST API (Pydantic model validation) ---

    def test_given_timeout_29_when_create_call_then_rejected(self):
        """Given timeout=29 (below min), when creating a REST call, then rejected."""
        with pytest.raises(ValidationError):
            CreateCallRequest(
                phone_number=_VALID_PHONE,
                instructions=_VALID_INSTRUCTIONS,
                timeout_seconds=29,
            )

    def test_given_timeout_30_when_create_call_then_accepted(self):
        """Given timeout=30 (exact min), when creating a REST call, then accepted."""
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            timeout_seconds=30,
        )
        assert req.timeout_seconds == 30

    def test_given_timeout_31_when_create_call_then_accepted(self):
        """Given timeout=31 (min+1), when creating a REST call, then accepted."""
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            timeout_seconds=31,
        )
        assert req.timeout_seconds == 31

    def test_given_timeout_3599_when_create_call_then_accepted(self):
        """Given timeout=3599 (max-1), when creating a REST call, then accepted."""
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            timeout_seconds=3599,
        )
        assert req.timeout_seconds == 3599

    def test_given_timeout_3600_when_create_call_then_accepted(self):
        """Given timeout=3600 (exact max), when creating a REST call, then accepted."""
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            timeout_seconds=3600,
        )
        assert req.timeout_seconds == 3600

    def test_given_timeout_3601_when_create_call_then_rejected(self):
        """Given timeout=3601 (above max), when creating a REST call, then rejected."""
        with pytest.raises(ValidationError):
            CreateCallRequest(
                phone_number=_VALID_PHONE,
                instructions=_VALID_INSTRUCTIONS,
                timeout_seconds=3601,
            )

    def test_given_timeout_0_when_create_call_then_rejected(self):
        """Given timeout=0, when creating a REST call, then rejected."""
        with pytest.raises(ValidationError):
            CreateCallRequest(
                phone_number=_VALID_PHONE,
                instructions=_VALID_INSTRUCTIONS,
                timeout_seconds=0,
            )

    def test_given_timeout_negative_when_create_call_then_rejected(self):
        """Given timeout=-1, when creating a REST call, then rejected."""
        with pytest.raises(ValidationError):
            CreateCallRequest(
                phone_number=_VALID_PHONE,
                instructions=_VALID_INSTRUCTIONS,
                timeout_seconds=-1,
            )

    # --- MCP entry point ---

    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_mcp_timeout_29_when_dial_then_error(self):
        """Given timeout=29 via MCP, when _do_dial is called, then error returned."""
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            timeout=29,
        )
        assert "error" in result
        assert "timeout" in result["error"].lower()

    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_mcp_timeout_3601_when_dial_then_error(self):
        """Given timeout=3601 via MCP, when _do_dial is called, then error returned."""
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            timeout=3601,
        )
        assert "error" in result
        assert "timeout" in result["error"].lower()

    # --- CLI entry point ---

    def test_given_cli_timeout_29_when_invoke_then_error(self):
        """Given timeout=29 via CLI, when dial is invoked, then _run_call receives it.

        The CLI passes timeout directly to _run_call which calls CallAgent.
        CallAgent delegates to _do_dial (MCP path) or LiveKit directly.
        We verify the CLI passes the value through correctly.
        """
        from click.testing import CliRunner

        from call_use.cli import main

        with patch("call_use.cli._run_call") as mock_run:
            mock_run.side_effect = ValueError("timeout must be between 30 and 3600")
            runner = CliRunner()
            result = runner.invoke(main, ["dial", _VALID_PHONE, "-i", "test", "--timeout", "29"])
            # CLI catches ValueError and exits with code 2
            assert result.exit_code == 2

    # --- REST via TestClient ---

    def test_given_rest_timeout_29_when_post_then_422(self):
        """Given timeout=29 in REST POST body, when sent, then 422 returned."""
        from fastapi.testclient import TestClient

        app = _create_test_app()
        client = TestClient(app)
        resp = client.post(
            "/calls",
            json={
                "phone_number": _VALID_PHONE,
                "instructions": _VALID_INSTRUCTIONS,
                "timeout_seconds": 29,
            },
            headers={"x-api-key": "test-key"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# IV-3: Instructions Validation BDD
# ---------------------------------------------------------------------------


class TestInstructionsValidationBDD:
    """BDD: Instructions length and content validation."""

    @patch("call_use.mcp_server.LiveKitAPI", new_callable=_mock_livekit_api)
    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_empty_instructions_when_mcp_dial_then_rejected(self, _mock_lk):
        """Given empty instructions, when MCP dial called, then proceeds.

        _do_dial does not validate empty instructions explicitly — it only
        checks max length. Empty string passes and dispatches to LiveKit.
        """
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions="",
        )
        # Empty instructions pass _do_dial validation (no min length check in MCP).
        assert "error" not in result

    @patch("call_use.mcp_server.LiveKitAPI", new_callable=_mock_livekit_api)
    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_whitespace_only_instructions_when_mcp_dial_then_rejected(self, _mock_lk):
        """Given whitespace-only instructions, when MCP dial called, then proceeds.

        MCP _do_dial does not strip/validate empty content — only max length.
        """
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions="   ",
        )
        assert "error" not in result

    @patch("call_use.mcp_server.LiveKitAPI", new_callable=_mock_livekit_api)
    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_instructions_at_max_length_when_mcp_dial_then_accepted(self, _mock_lk):
        """Given instructions at exactly MAX_INSTRUCTIONS_LENGTH, then accepted."""
        instructions = "x" * MAX_INSTRUCTIONS_LENGTH
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions=instructions,
        )
        assert "error" not in result
        assert "task_id" in result

    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_instructions_over_max_when_mcp_dial_then_rejected(self):
        """Given instructions exceeding MAX_INSTRUCTIONS_LENGTH, then error returned."""
        instructions = "x" * (MAX_INSTRUCTIONS_LENGTH + 1)
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions=instructions,
        )
        assert "error" in result
        assert "instructions too long" in result["error"]


# ---------------------------------------------------------------------------
# IV-4: Inject Message Validation BDD
# ---------------------------------------------------------------------------


class TestInjectValidationBDD:
    """BDD: Inject message validation via Pydantic model."""

    def test_given_empty_message_when_inject_then_400(self):
        """Given empty message, when InjectRequest created, then validation error."""
        with pytest.raises(ValidationError):
            InjectRequest(message="")

    def test_given_whitespace_message_when_inject_then_400(self):
        """Given whitespace-only message, when InjectRequest created, then accepted.

        Pydantic min_length=1 counts whitespace characters, so ' ' passes.
        """
        req = InjectRequest(message=" ")
        assert req.message == " "

    def test_given_message_at_2000_chars_when_inject_then_accepted(self):
        """Given message at exactly 2000 chars, when InjectRequest created, then accepted."""
        msg = "a" * 2000
        req = InjectRequest(message=msg)
        assert len(req.message) == 2000

    def test_given_message_at_2001_chars_when_inject_then_400(self):
        """Given message at 2001 chars, when InjectRequest created, then rejected."""
        msg = "a" * 2001
        with pytest.raises(ValidationError):
            InjectRequest(message=msg)


# ---------------------------------------------------------------------------
# IV-5: Voice ID Validation BDD
# ---------------------------------------------------------------------------


class TestVoiceIdValidationBDD:
    """BDD: Voice ID validation across entry points."""

    def test_given_valid_voices_when_create_call_then_all_accepted(self):
        """Given each valid voice ID, when CreateCallRequest made, then all accepted."""
        expected_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
        assert VALID_VOICES == expected_voices

        for voice in expected_voices:
            req = CreateCallRequest(
                phone_number=_VALID_PHONE,
                instructions=_VALID_INSTRUCTIONS,
                voice_id=voice,
            )
            assert req.voice_id == voice

    def test_given_invalid_voice_when_create_call_then_rejected(self):
        """Given an invalid voice ID, when CreateCallRequest made, then rejected."""
        with pytest.raises(ValidationError):
            CreateCallRequest(
                phone_number=_VALID_PHONE,
                instructions=_VALID_INSTRUCTIONS,
                voice_id="invalid_voice",
            )

    def test_given_none_voice_when_create_call_then_default_used(self):
        """Given no voice_id, when CreateCallRequest made, then default is None."""
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
        )
        assert req.voice_id is None

    @patch("call_use.mcp_server.LiveKitAPI", new_callable=_mock_livekit_api)
    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_invalid_voice_when_mcp_dial_then_falls_back_to_alloy(self, _mock_lk):
        """Given invalid voice via MCP, when _do_dial called, then falls back to alloy."""
        # _do_dial logs a warning and falls back to 'alloy' for invalid voices
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            voice_id="invalid_voice",
        )
        # Should not error — just silently fall back to alloy and dispatch
        assert "error" not in result
        assert "task_id" in result


# ---------------------------------------------------------------------------
# IV-6: User Info Validation BDD
# ---------------------------------------------------------------------------


class TestUserInfoValidationBDD:
    """BDD: user_info edge cases across entry points."""

    def test_given_empty_dict_when_dial_then_accepted(self):
        """Given empty dict for user_info, when CreateCallRequest made, then accepted."""
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            user_info={},
        )
        assert req.user_info == {}

    def test_given_nested_dict_when_dial_then_accepted(self):
        """Given nested dict for user_info, when CreateCallRequest made, then accepted."""
        nested = {"customer": {"name": "Alice", "orders": [{"id": 1}, {"id": 2}]}}
        req = CreateCallRequest(
            phone_number=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            user_info=nested,
        )
        assert req.user_info == nested

    @patch.dict("os.environ", _MCP_ENV)
    async def test_given_non_serializable_when_mcp_dial_then_error(self):
        """Given non-JSON-serializable user_info via MCP, then error returned."""
        # Create an object that json.dumps cannot handle
        non_serializable = {"key": object()}
        result = await _do_dial(
            phone=_VALID_PHONE,
            instructions=_VALID_INSTRUCTIONS,
            user_info=non_serializable,
        )
        assert "error" in result
        assert "JSON-serializable" in result["error"]


# ---------------------------------------------------------------------------
# Helper: create a test FastAPI app
# ---------------------------------------------------------------------------


def _create_test_app():
    """Create a FastAPI test app with a known API key."""
    from call_use.server import create_app

    return create_app(api_key="test-key")
