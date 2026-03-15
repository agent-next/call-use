"""Tests for call-use CLI and __init__ lazy imports."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from call_use.cli import main

pytestmark = pytest.mark.unit


# ===========================================================================
# __init__.py lazy imports (lines 41-45)
# ===========================================================================


class TestLazyImports:
    def test_mcp_server_lazy_import(self):
        """Accessing call_use.mcp_server triggers lazy import (lines 41-44)."""
        import call_use

        # Call __getattr__ directly to test the mcp_server branch
        result = call_use.__getattr__("mcp_server")
        assert result is not None

    def test_create_app_lazy_import(self):
        """Accessing call_use.create_app triggers lazy import."""
        import call_use

        if "create_app" in call_use.__dict__:
            saved = call_use.__dict__.pop("create_app")
        else:
            saved = None
        try:
            create_app = call_use.create_app
            assert callable(create_app)
        finally:
            if saved is not None:
                call_use.__dict__["create_app"] = saved

    def test_nonexistent_attr_raises(self):
        """Accessing a nonexistent attribute raises AttributeError (line 45)."""
        import call_use

        with pytest.raises(AttributeError, match="no attribute"):
            _ = call_use.nonexistent_thing


def _extract_json(output: str) -> dict:
    """Extract JSON object from CLI output (ignoring stderr lines mixed in)."""
    # Find the JSON block in the output — it starts with '{'
    lines = output.strip().split("\n")
    json_lines = []
    in_json = False
    for line in lines:
        if line.strip().startswith("{"):
            in_json = True
        if in_json:
            json_lines.append(line)
    return json.loads("\n".join(json_lines))


def test_dial_missing_phone_shows_error():
    runner = CliRunner()
    result = runner.invoke(main, ["dial"])
    assert result.exit_code != 0


def test_dial_missing_instructions_shows_error():
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234"])
    assert result.exit_code != 0


@patch("call_use.cli._run_call")
def test_dial_valid_args_calls_agent(mock_run):
    mock_run.return_value = {
        "task_id": "test-123",
        "disposition": "completed",
        "duration_seconds": 42.0,
        "transcript": [],
        "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    output = _extract_json(result.output)
    assert output["disposition"] == "completed"


@patch("call_use.cli._run_call")
def test_dial_with_user_info(mock_run):
    mock_run.return_value = {
        "task_id": "test-456",
        "disposition": "completed",
        "duration_seconds": 10.0,
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
            '{"name": "Alice", "account": "12345"}',
        ],
    )
    assert result.exit_code == 0
    call_kwargs = mock_run.call_args
    assert call_kwargs[1]["user_info"] == {"name": "Alice", "account": "12345"}


@patch("call_use.cli._run_call")
def test_dial_failed_returns_nonzero(mock_run):
    mock_run.return_value = {
        "task_id": "test-789",
        "disposition": "failed",
        "duration_seconds": 5.0,
        "transcript": [],
        "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 1


@patch("call_use.cli._run_call")
def test_dial_voicemail_returns_zero(mock_run):
    mock_run.return_value = {
        "task_id": "test-vm",
        "disposition": "voicemail",
        "duration_seconds": 15.0,
        "transcript": [],
        "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 0
    output = _extract_json(result.output)
    assert output["disposition"] == "voicemail"


@patch("call_use.cli._run_call")
def test_dial_no_answer_returns_zero(mock_run):
    mock_run.return_value = {
        "task_id": "test-na",
        "disposition": "no_answer",
        "duration_seconds": 30.0,
        "transcript": [],
        "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 0


@patch("call_use.cli._run_call")
def test_dial_runtime_error_exits_1(mock_run):
    """Runtime errors (network, LiveKit down) exit 1, not 2."""
    mock_run.side_effect = RuntimeError("LiveKit connection refused")
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
    assert result.exit_code == 1  # NOT 2 (input error)
    assert "LiveKit connection refused" in result.output


def test_dial_invalid_json_user_info_exits_2():
    """Malformed --user-info JSON exits 2 (input error)."""
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test", "-u", "not-json"])
    assert result.exit_code == 2


@patch("call_use.cli._run_call")
def test_dial_missing_env_vars_shows_helpful_error(mock_run):
    """Missing env vars should show clear error with instructions."""
    mock_run.side_effect = RuntimeError("Missing required environment variables:\n  LIVEKIT_URL")
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
    assert result.exit_code == 1
    assert "LIVEKIT_URL" in result.output


@patch("call_use.cli._run_call")
def test_dial_value_error_shows_invalid_phone(mock_run):
    """ValueError from phone validation shows 'Invalid phone number'."""
    mock_run.side_effect = ValueError("Not a valid E.164 number")
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "bad-number", "-i", "test"])
    assert result.exit_code == 2
    assert "Invalid phone number" in result.output


@patch("call_use.cli._run_call")
def test_dial_connection_error_shows_livekit_message(mock_run):
    """ConnectionError shows 'Could not connect to LiveKit'."""
    mock_run.side_effect = ConnectionError("Connection refused")
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
    assert result.exit_code == 1
    assert "Could not connect to LiveKit" in result.output


@patch.dict(os.environ, {}, clear=True)
def test_check_env_raises_on_missing_vars():
    """_check_env raises RuntimeError listing all missing vars."""
    from call_use.cli import _check_env

    try:
        _check_env()
        assert False, "_check_env should have raised"  # noqa: B011
    except RuntimeError as e:
        msg = str(e)
        assert "LIVEKIT_URL" in msg
        assert "OPENAI_API_KEY" in msg
        assert "DEEPGRAM_API_KEY" in msg
        assert "https://github.com/agent-next/call-use#configure" in msg


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "OPENAI_API_KEY": "sk-test",
        "DEEPGRAM_API_KEY": "dg-test",
    },
)
def test_check_env_passes_when_all_set():
    """_check_env does not raise when all vars are set."""
    from call_use.cli import _check_env

    _check_env()  # Should not raise


def test_auth_command_not_registered():
    """auth command removed for v0.1 -- only dial should be registered."""
    from click.testing import CliRunner

    from call_use.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["auth"])
    assert result.exit_code != 0


# ===========================================================================
# _event_printer
# ===========================================================================


class TestEventPrinter:
    def test_prints_transcript_event(self, capsys):
        from call_use.cli import _event_printer
        from call_use.models import CallEvent, CallEventType

        event = CallEvent(
            type=CallEventType.transcript,
            data={"speaker": "agent", "text": "Hello there"},
        )
        _event_printer(event)
        captured = capsys.readouterr()
        assert "[agent] Hello there" in captured.err

    def test_prints_state_change_event(self, capsys):
        from call_use.cli import _event_printer
        from call_use.models import CallEvent, CallEventType

        event = CallEvent(
            type=CallEventType.state_change,
            data={"from": "dialing", "to": "connected"},
        )
        _event_printer(event)
        captured = capsys.readouterr()
        assert "state: connected" in captured.err

    def test_prints_approval_request_event(self, capsys):
        from call_use.cli import _event_printer
        from call_use.models import CallEvent, CallEventType

        event = CallEvent(
            type=CallEventType.approval_request,
            data={"details": "Refund of $50", "approval_id": "apr-1"},
        )
        _event_printer(event)
        captured = capsys.readouterr()
        assert "APPROVAL NEEDED" in captured.err
        assert "Refund of $50" in captured.err


# ===========================================================================
# _stdin_approval_handler
# ===========================================================================


class TestStdinApprovalHandler:
    def test_approve_returns_approved(self):
        """_stdin_approval_handler returns 'approved' when user enters 'y'."""
        from call_use.cli import _stdin_approval_handler

        with patch("call_use.cli.click.prompt", return_value="y"):
            result = _stdin_approval_handler({"details": "Refund of $50"})
        assert result == "approved"

    def test_reject_returns_rejected(self):
        """_stdin_approval_handler returns 'rejected' when user enters 'n'."""
        from call_use.cli import _stdin_approval_handler

        with patch("call_use.cli.click.prompt", return_value="n"):
            result = _stdin_approval_handler({"details": "Expensive thing"})
        assert result == "rejected"

    def test_handler_with_non_dict_data(self):
        """_stdin_approval_handler handles non-dict data by converting to str."""
        from call_use.cli import _stdin_approval_handler

        with patch("call_use.cli.click.prompt", return_value="y"):
            result = _stdin_approval_handler("plain string data")
        assert result == "approved"

    def test_handler_dict_without_details(self):
        """_stdin_approval_handler falls back to str(data) when no 'details' key."""
        from call_use.cli import _stdin_approval_handler

        with patch("call_use.cli.click.prompt", return_value="n"):
            result = _stdin_approval_handler({"other_key": "value"})
        assert result == "rejected"


# ===========================================================================
# dial with --approval-required flag
# ===========================================================================


@patch("call_use.cli._run_call")
def test_dial_with_approval_required(mock_run):
    """dial --approval-required passes approval_required=True to _run_call."""
    mock_run.return_value = {
        "task_id": "test-apr",
        "disposition": "completed",
        "duration_seconds": 30.0,
        "transcript": [],
        "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["dial", "+18005551234", "-i", "Test", "--approval-required"],
    )
    assert result.exit_code == 0
    call_kwargs = mock_run.call_args
    assert call_kwargs[1]["approval_required"] is True


@patch("call_use.cli._run_call")
def test_dial_generic_exception_exits_1(mock_run):
    """Unexpected exceptions exit 1 with error message."""
    mock_run.side_effect = Exception("Unexpected error")
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
    assert result.exit_code == 1
    assert "Unexpected error" in result.output


# ===========================================================================
# _run_call (lines 62-84)
# ===========================================================================


# ===========================================================================
# doctor command
# ===========================================================================


_ALL_DOCTOR_ENV = {
    "LIVEKIT_URL": "wss://test",
    "LIVEKIT_API_KEY": "key",
    "LIVEKIT_API_SECRET": "secret",
    "SIP_TRUNK_ID": "trunk",
    "OPENAI_API_KEY": "sk-test",
    "DEEPGRAM_API_KEY": "dg-test",
}


class TestDoctor:
    @patch("call_use.cli._check_livekit_connectivity", return_value=(True, "LiveKit connection OK"))
    @patch.dict(os.environ, _ALL_DOCTOR_ENV, clear=True)
    def test_doctor_all_vars_set_shows_success(self, mock_lk):
        """All env vars set + LiveKit OK → exit 0, all checks pass."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "7 passed, 0 failed" in result.output
        assert "LiveKit connection OK" in result.output

    @patch("call_use.cli._check_livekit_connectivity", return_value=(True, "LiveKit connection OK"))
    @patch.dict(os.environ, {k: v for k, v in _ALL_DOCTOR_ENV.items() if k != "DEEPGRAM_API_KEY"}, clear=True)
    def test_doctor_missing_vars_shows_failure(self, mock_lk):
        """Missing DEEPGRAM_API_KEY → exit 1, shows failure."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 1
        assert "DEEPGRAM_API_KEY missing" in result.output
        assert "1 failed" in result.output

    @patch("call_use.cli._check_livekit_connectivity", return_value=(False, "LiveKit connection failed: Connection refused"))
    @patch.dict(os.environ, _ALL_DOCTOR_ENV, clear=True)
    def test_doctor_livekit_connection_failure(self, mock_lk):
        """LiveKit connection failure → shows error, doesn't crash, exit 1."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 1
        assert "LiveKit connection failed" in result.output
        assert "1 failed" in result.output


# ===========================================================================
# _run_call (lines 62-84)
# ===========================================================================


class TestRunCall:
    @patch("call_use.cli.asyncio.run")
    @patch("call_use.cli._check_env")
    @patch("call_use.cli.load_dotenv", create=True)
    def test_run_call_basic(self, mock_dotenv, mock_check, mock_async_run):
        """_run_call creates CallAgent and calls asyncio.run."""
        from call_use.cli import _run_call

        mock_outcome = MagicMock()
        mock_outcome.model_dump.return_value = {
            "task_id": "test-1",
            "disposition": "completed",
            "duration_seconds": 10.0,
            "transcript": [],
            "events": [],
        }
        mock_async_run.return_value = mock_outcome

        with patch("call_use.sdk.CallAgent") as MockAgent:
            MockAgent.return_value.call = AsyncMock(return_value=mock_outcome)
            # _run_call imports CallAgent inside, so we need to patch at import target
            with patch("call_use.cli.CallAgent", MockAgent, create=True):
                result = _run_call(
                    phone="+12025551234",
                    instructions="Test call",
                    approval_required=False,
                )

        assert result == mock_outcome.model_dump.return_value

    @patch("call_use.cli.asyncio.run")
    @patch("call_use.cli._check_env")
    @patch("call_use.cli.load_dotenv", create=True)
    def test_run_call_with_approval(self, mock_dotenv, mock_check, mock_async_run):
        """_run_call passes on_approval when approval_required=True."""
        from call_use.cli import _run_call

        mock_outcome = MagicMock()
        mock_outcome.model_dump.return_value = {"disposition": "completed"}
        mock_async_run.return_value = mock_outcome

        with patch("call_use.sdk.CallAgent") as MockAgent:
            MockAgent.return_value.call = AsyncMock(return_value=mock_outcome)
            _run_call(
                phone="+12025551234",
                instructions="Test",
                approval_required=True,
            )

        # Verify on_approval was passed
        call_kwargs = MockAgent.call_args.kwargs
        assert call_kwargs["approval_required"] is True
        assert call_kwargs["on_approval"] is not None
