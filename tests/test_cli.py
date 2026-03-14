"""Tests for call-use CLI."""

import json
import os
from unittest.mock import patch

from click.testing import CliRunner

from call_use.cli import main


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
        assert "https://github.com/agent-next/call-use#configure" in msg


@patch.dict(
    os.environ,
    {
        "LIVEKIT_URL": "wss://test",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "SIP_TRUNK_ID": "trunk",
        "OPENAI_API_KEY": "sk-test",
    },
)
def test_check_env_passes_when_all_set():
    """_check_env does not raise when all vars are set."""
    from call_use.cli import _check_env

    _check_env()  # Should not raise
