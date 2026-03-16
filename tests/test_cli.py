"""Tests for call-use CLI and __init__ lazy imports."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from call_use.cli import main
from call_use.models import CallError, CallErrorCode

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
    # Find the JSON block in the output -- it starts with '{'
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
    """_check_env raises RuntimeError listing all missing vars (default openai provider)."""
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
        "CALL_USE_LLM_PROVIDER": "openai",
    },
)
def test_check_env_passes_when_all_set():
    """_check_env does not raise when all vars are set."""
    from call_use.cli import _check_env

    _check_env()  # Should not raise


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "GOOGLE_API_KEY": "goog-test",
        "DEEPGRAM_API_KEY": "dg-test",
        "CALL_USE_LLM_PROVIDER": "google",
    },
)
def test_check_env_passes_for_google_provider():
    """_check_env does not raise for google provider with correct keys."""
    from call_use.cli import _check_env

    _check_env()  # Should not raise


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "DEEPGRAM_API_KEY": "dg-test",
        "CALL_USE_LLM_PROVIDER": "grok",
    },
)
def test_check_env_raises_for_grok_missing_keys():
    """_check_env raises for grok provider missing XAI_API_KEY."""
    from call_use.cli import _check_env

    with pytest.raises(RuntimeError, match="XAI_API_KEY"):
        _check_env()


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "XAI_API_KEY": "xai-test",
        "DEEPGRAM_API_KEY": "dg-test",
        "CALL_USE_LLM_PROVIDER": "grok",
    },
)
def test_check_env_raises_for_grok_missing_openai_tts_key():
    """_check_env raises for grok when OPENAI_API_KEY (TTS) is missing."""
    from call_use.cli import _check_env

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _check_env()


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "XAI_API_KEY": "xai-test",
        "OPENAI_API_KEY": "sk-test",
        "DEEPGRAM_API_KEY": "dg-test",
        "CALL_USE_LLM_PROVIDER": "grok",
    },
)
def test_check_env_passes_for_grok_all_keys():
    """_check_env passes for grok with both XAI and OPENAI keys."""
    from call_use.cli import _check_env

    _check_env()  # Should not raise


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "OPENROUTER_API_KEY": "or-test",
        "DEEPGRAM_API_KEY": "dg-test",
        "CALL_USE_LLM_PROVIDER": "openrouter",
    },
)
def test_check_env_raises_for_openrouter_missing_openai_tts_key():
    """_check_env raises for openrouter when OPENAI_API_KEY (TTS) is missing."""
    from call_use.cli import _check_env

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _check_env()


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "OPENROUTER_API_KEY": "or-test",
        "OPENAI_API_KEY": "sk-test",
        "DEEPGRAM_API_KEY": "dg-test",
        "CALL_USE_LLM_PROVIDER": "openrouter",
    },
)
def test_check_env_passes_for_openrouter_all_keys():
    """_check_env passes for openrouter with both keys."""
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
    "CALL_USE_LLM_PROVIDER": "openai",
}


class TestDoctor:
    @patch("call_use.cli._check_livekit_connectivity", return_value=(True, "LiveKit connection OK"))
    @patch.dict(os.environ, _ALL_DOCTOR_ENV, clear=True)
    def test_doctor_all_vars_set_shows_success(self, mock_lk):
        """All env vars set + LiveKit OK -> exit 0, all checks pass."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "7 passed, 0 failed" in result.output
        assert "LiveKit connection OK" in result.output

    @patch(
        "call_use.cli._check_livekit_connectivity",
        return_value=(True, "LiveKit connection OK"),
    )
    @patch.dict(
        os.environ,
        {k: v for k, v in _ALL_DOCTOR_ENV.items() if k != "DEEPGRAM_API_KEY"},
        clear=True,
    )
    def test_doctor_missing_vars_shows_failure(self, mock_lk):
        """Missing DEEPGRAM_API_KEY -> exit 1, shows failure."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 1
        assert "DEEPGRAM_API_KEY missing" in result.output
        assert "1 failed" in result.output

    @patch(
        "call_use.cli._check_livekit_connectivity",
        return_value=(
            False,
            "LiveKit connection failed: Connection refused",
        ),
    )
    @patch.dict(os.environ, _ALL_DOCTOR_ENV, clear=True)
    def test_doctor_livekit_connection_failure(self, mock_lk):
        """LiveKit connection failure -> shows error, doesn't crash, exit 1."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 1
        assert "LiveKit connection failed" in result.output
        assert "1 failed" in result.output

    @patch("call_use.cli._check_livekit_connectivity", return_value=(True, "LiveKit connection OK"))
    @patch.dict(
        os.environ,
        {
            "LIVEKIT_URL": "wss://test",
            "LIVEKIT_API_KEY": "key",
            "LIVEKIT_API_SECRET": "secret",
            "SIP_TRUNK_ID": "trunk",
            "GOOGLE_API_KEY": "goog-test",
            "DEEPGRAM_API_KEY": "dg-test",
            "CALL_USE_LLM_PROVIDER": "google",
        },
        clear=True,
    )
    def test_doctor_google_provider_checks_google_key(self, mock_lk):
        """Doctor with google provider checks GOOGLE_API_KEY, not OPENAI."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "GOOGLE_API_KEY set" in result.output
        assert "OPENAI_API_KEY" not in result.output

    @patch.dict(
        os.environ,
        {
            k: v
            for k, v in _ALL_DOCTOR_ENV.items()
            if k
            not in (
                "LIVEKIT_URL",
                "LIVEKIT_API_KEY",
                "LIVEKIT_API_SECRET",
            )
        },
        clear=True,
    )
    def test_doctor_livekit_skipped_when_creds_missing(self):
        """Missing LiveKit credentials -> connectivity check skipped, exit 1."""
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 1
        assert "LiveKit connectivity skipped" in result.output


class TestCheckLivekitConnectivity:
    def test_success_path(self):
        """_check_livekit_connectivity returns (True, ...) when probe succeeds."""
        from call_use.cli import _check_livekit_connectivity

        mock_lkapi = AsyncMock()
        mock_lkapi.__aenter__ = AsyncMock(return_value=mock_lkapi)
        mock_lkapi.__aexit__ = AsyncMock(return_value=False)
        mock_lkapi.room.list_rooms = AsyncMock(return_value=[])

        with patch.dict("sys.modules", {"livekit": MagicMock(), "livekit.api": MagicMock()}):
            with patch("livekit.api.LiveKitAPI", return_value=mock_lkapi):
                ok, msg = _check_livekit_connectivity()
        assert ok is True
        assert "LiveKit connection OK" in msg

    def test_failure_path(self):
        """_check_livekit_connectivity returns (False, ...) when probe raises."""
        from call_use.cli import _check_livekit_connectivity

        mock_lkapi = AsyncMock()
        mock_lkapi.__aenter__ = AsyncMock(return_value=mock_lkapi)
        mock_lkapi.__aexit__ = AsyncMock(return_value=False)
        mock_lkapi.room.list_rooms = AsyncMock(side_effect=Exception("Connection refused"))

        with patch.dict("sys.modules", {"livekit": MagicMock(), "livekit.api": MagicMock()}):
            with patch("livekit.api.LiveKitAPI", return_value=mock_lkapi):
                ok, msg = _check_livekit_connectivity()
        assert ok is False
        assert "LiveKit connection failed" in msg
        assert "Connection refused" in msg


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


# ===========================================================================
# Worker not running -- CallError handling
# ===========================================================================


@patch("call_use.cli._run_call")
def test_dial_worker_not_running_shows_actionable_error(mock_run):
    """CallError with worker_not_running shows clear start instructions."""
    mock_run.side_effect = CallError(
        code=CallErrorCode.worker_not_running,
        message="No call-use-worker picked up the job within 10s.",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
    assert result.exit_code == 1
    assert "No worker available" in result.output
    assert "call-use-worker start" in result.output


def test_dial_timeout_out_of_range_rejected():
    """--timeout outside 30-3600 is rejected by Click IntRange."""
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test", "--timeout", "10"])
    assert result.exit_code != 0

    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test", "--timeout", "5000"])
    assert result.exit_code != 0


@patch("call_use.cli._run_call")
def test_dial_other_call_error_shows_generic_message(mock_run):
    """CallError with a non-worker code shows generic error message."""
    mock_run.side_effect = CallError(
        code=CallErrorCode.dial_failed,
        message="SIP trunk not responding",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "-i", "test"])
    assert result.exit_code == 1
    assert "SIP trunk not responding" in result.output


# ===========================================================================
# setup command
# ===========================================================================


class TestSetup:
    """Tests for the interactive setup wizard."""

    def _make_required_input(
        self,
        livekit_url="wss://my-app.livekit.cloud",
        livekit_key="APIxxx",
        livekit_secret="secretval",
        sip_trunk="ST_xxxx",
        provider_choice="1",
        openai_key="sk-testabc",
        deepgram_key="dg-testabc",
        api_key="",
    ):
        """Build stdin input for the setup wizard (OpenAI default)."""
        lines = [
            livekit_url,
            livekit_key,
            livekit_secret,
            sip_trunk,
            provider_choice,  # LLM provider selection
            openai_key,  # provider-specific key(s)
            deepgram_key,
            api_key,  # optional API_KEY (empty = skip)
        ]
        return "\n".join(lines) + "\n"

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_writes_env_file(self, mock_dotenv, tmp_path):
        """Setup writes .env with all required keys (default OpenAI provider)."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["setup"], input=self._make_required_input())
            assert result.exit_code == 0
            assert "Created .env with 7 variables" in result.output

            env_content = open(".env").read()
            assert "# Generated by call-use setup" in env_content
            assert "LIVEKIT_URL=wss://my-app.livekit.cloud" in env_content
            assert "LIVEKIT_API_KEY=APIxxx" in env_content
            assert "LIVEKIT_API_SECRET=secretval" in env_content
            assert "SIP_TRUNK_ID=ST_xxxx" in env_content
            assert "CALL_USE_LLM_PROVIDER=openai" in env_content
            assert "OPENAI_API_KEY=sk-testabc" in env_content
            assert "DEEPGRAM_API_KEY=dg-testabc" in env_content

            # .env should have restricted permissions (secrets inside)
            mode = os.stat(".env").st_mode & 0o777
            assert mode == 0o600, f".env permissions should be 0o600, got {oct(mode)}"

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_openrouter_provider(self, mock_dotenv, tmp_path):
        """Setup with OpenRouter provider asks for OPENROUTER + OPENAI keys."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            lines = [
                "wss://app.livekit.cloud",
                "APIxxx",
                "secretval",
                "ST_xxxx",
                "2",  # OpenRouter
                "or-key-123",  # OPENROUTER_API_KEY
                "sk-ttskey",  # OPENAI_API_KEY for TTS
                "dg-testabc",
                "",  # skip optional
            ]
            result = runner.invoke(main, ["setup"], input="\n".join(lines) + "\n")
            assert result.exit_code == 0

            env_content = open(".env").read()
            assert "CALL_USE_LLM_PROVIDER=openrouter" in env_content
            assert "OPENROUTER_API_KEY=or-key-123" in env_content
            assert "OPENAI_API_KEY=sk-ttskey" in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_google_provider(self, mock_dotenv, tmp_path):
        """Setup with Google Gemini provider asks for GOOGLE_API_KEY."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            lines = [
                "wss://app.livekit.cloud",
                "APIxxx",
                "secretval",
                "ST_xxxx",
                "3",  # Google Gemini
                "AIza-google-key",  # GOOGLE_API_KEY
                "dg-testabc",
                "",  # skip optional
            ]
            result = runner.invoke(main, ["setup"], input="\n".join(lines) + "\n")
            assert result.exit_code == 0

            env_content = open(".env").read()
            assert "CALL_USE_LLM_PROVIDER=google" in env_content
            assert "GOOGLE_API_KEY=AIza-google-key" in env_content
            assert "OPENAI_API_KEY" not in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_grok_provider(self, mock_dotenv, tmp_path):
        """Setup with Grok provider asks for XAI_API_KEY + OPENAI_API_KEY."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            lines = [
                "wss://app.livekit.cloud",
                "APIxxx",
                "secretval",
                "ST_xxxx",
                "4",  # Grok
                "xai-key-123",  # XAI_API_KEY
                "sk-ttskey",  # OPENAI_API_KEY for TTS
                "dg-testabc",
                "",  # skip optional
            ]
            result = runner.invoke(main, ["setup"], input="\n".join(lines) + "\n")
            assert result.exit_code == 0

            env_content = open(".env").read()
            assert "CALL_USE_LLM_PROVIDER=grok" in env_content
            assert "XAI_API_KEY=xai-key-123" in env_content
            assert "OPENAI_API_KEY=sk-ttskey" in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_with_optional_key(self, mock_dotenv, tmp_path):
        """Setup includes optional API_KEY when provided."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                main,
                ["setup"],
                input=self._make_required_input(api_key="my-api-key"),
            )
            assert result.exit_code == 0
            assert "Created .env with 8 variables" in result.output
            env_content = open(".env").read()
            assert "API_KEY=my-api-key" in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_optional_key_skipped(self, mock_dotenv, tmp_path):
        """Optional keys show skip message when Enter is pressed."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["setup"], input=self._make_required_input())
            assert result.exit_code == 0
            assert "API_KEY skipped" in result.output

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_existing_env_overwrite_yes(self, mock_dotenv, tmp_path):
        """Existing .env with overwrite=y proceeds normally."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            open(".env", "w").write("OLD=value\n")
            # 'y' for overwrite + normal required + optional input
            inp = "y\n" + self._make_required_input()
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            assert "Created .env with 7 variables" in result.output
            env_content = open(".env").read()
            assert "OLD=value" not in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_existing_env_overwrite_no(self, mock_dotenv, tmp_path):
        """Existing .env with overwrite=n aborts."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            open(".env", "w").write("OLD=value\n")
            result = runner.invoke(main, ["setup"], input="n\n")
            assert result.exit_code == 0
            assert "Aborted" in result.output
            # Original file untouched
            assert open(".env").read() == "OLD=value\n"

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_livekit_url_validation(self, mock_dotenv, tmp_path):
        """LIVEKIT_URL must start with wss:// or ws://."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First enter invalid, then valid
            inp = "http://bad.url\nwss://good.livekit.cloud\n"
            inp += "APIxxx\nsecretval\nST_xxxx\n"
            inp += "1\nsk-testabc\ndg-testabc\n\n"
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            assert "Must start with wss:// or ws://" in result.output
            env_content = open(".env").read()
            assert "LIVEKIT_URL=wss://good.livekit.cloud" in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_openai_key_validation(self, mock_dotenv, tmp_path):
        """OPENAI_API_KEY must start with sk-."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            inp = "wss://app.livekit.cloud\nAPIxxx\nsecretval\nST_xxxx\n"
            inp += "1\nbad-key\nsk-goodkey\n"  # provider 1, first invalid, then valid
            inp += "dg-testabc\n\n"
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            assert "Must start with sk-" in result.output
            env_content = open(".env").read()
            assert "OPENAI_API_KEY=sk-goodkey" in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {"LIVEKIT_URL": "wss://existing.value"}, clear=True)
    def test_setup_shows_existing_env_as_default(self, mock_dotenv, tmp_path):
        """Existing env vars appear as defaults in prompts."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Press enter to accept existing LIVEKIT_URL default, provide rest
            inp = "\nAPIxxx\nsecretval\nST_xxxx\n1\nsk-testabc\ndg-testabc\n\n"
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            env_content = open(".env").read()
            assert "LIVEKIT_URL=wss://existing.value" in env_content

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_runs_doctor_verification(self, mock_dotenv, tmp_path):
        """Setup runs verification after writing .env."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["setup"], input=self._make_required_input())
            assert result.exit_code == 0
            assert "Running call-use doctor..." in result.output
            assert "Setup complete!" in result.output

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_empty_required_key_retries(self, mock_dotenv, tmp_path):
        """Empty required key shows error and re-prompts."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Empty LIVEKIT_URL first, then valid
            inp = "\nwss://ok.livekit.cloud\nAPIxxx\nsecretval\nST_xxxx\n"
            inp += "1\nsk-testabc\ndg-testabc\n\n"
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            assert "LIVEKIT_URL is required" in result.output

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_invalid_provider_choice_retries(self, mock_dotenv, tmp_path):
        """Invalid provider choice shows error and re-prompts."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            inp = "wss://app.livekit.cloud\nAPIxxx\nsecretval\nST_xxxx\n"
            inp += "9\n1\nsk-testabc\ndg-testabc\n\n"  # invalid then valid
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            assert "Invalid choice" in result.output

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_google_provider_verification_checks_google_key(self, tmp_path):
        """Setup verification shows GOOGLE_API_KEY for google provider."""

        def _fake_load_dotenv(*args, **kwargs):
            """Simulate load_dotenv by reading .env and setting os.environ."""
            from pathlib import Path

            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if kwargs.get("override") or k not in os.environ:
                            os.environ[k] = v

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            lines = [
                "wss://app.livekit.cloud",
                "APIxxx",
                "secretval",
                "ST_xxxx",
                "3",
                "AIza-google-key",
                "dg-testabc",
                "",
            ]
            with patch("dotenv.load_dotenv", side_effect=_fake_load_dotenv):
                result = runner.invoke(main, ["setup"], input="\n".join(lines) + "\n")
            assert result.exit_code == 0
            assert "GOOGLE_API_KEY set" in result.output

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_sanitizes_newlines_in_env_values(self, mock_dotenv, tmp_path):
        """Values with embedded carriage returns are sanitized in .env."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                main,
                ["setup"],
                input=self._make_required_input(),
            )
            assert result.exit_code == 0
            env_content = open(".env").read()
            for line in env_content.strip().split("\n"):
                assert "=" in line or line.startswith("#"), f"Malformed line: {line}"

    @patch("call_use.cli.load_dotenv", create=True)
    @patch.dict(os.environ, {"API_KEY": "existing-api-key"}, clear=True)
    def test_setup_optional_key_shows_existing_default(self, mock_dotenv, tmp_path):
        """Optional key shows existing env value as default."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            inp = "wss://app.livekit.cloud\nAPIxxx\nsecretval\nST_xxxx\n"
            inp += "1\nsk-testabc\ndg-testabc\n\n"  # accept default optional
            result = runner.invoke(main, ["setup"], input=inp)
            assert result.exit_code == 0
            env_content = open(".env").read()
            assert "API_KEY=existing-api-key" in env_content


# ===========================================================================
# _get_env_vars_for_provider
# ===========================================================================


class TestGetEnvVarsForProvider:
    def test_openai_provider(self):
        from call_use.cli import _get_env_vars_for_provider

        result = _get_env_vars_for_provider("openai")
        assert "OPENAI_API_KEY" in result
        assert "LIVEKIT_URL" in result
        assert "DEEPGRAM_API_KEY" in result

    def test_google_provider(self):
        from call_use.cli import _get_env_vars_for_provider

        result = _get_env_vars_for_provider("google")
        assert "GOOGLE_API_KEY" in result
        assert "OPENAI_API_KEY" not in result

    def test_grok_provider(self):
        from call_use.cli import _get_env_vars_for_provider

        result = _get_env_vars_for_provider("grok")
        assert "XAI_API_KEY" in result
        assert "OPENAI_API_KEY" in result

    def test_openrouter_provider(self):
        from call_use.cli import _get_env_vars_for_provider

        result = _get_env_vars_for_provider("openrouter")
        assert "OPENROUTER_API_KEY" in result
        assert "OPENAI_API_KEY" in result

    def test_unknown_provider_falls_back_to_openai(self):
        from call_use.cli import _get_env_vars_for_provider

        result = _get_env_vars_for_provider("unknown")
        assert "OPENAI_API_KEY" in result
