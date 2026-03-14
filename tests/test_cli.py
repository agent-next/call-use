"""Tests for call-use CLI."""
import json
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
        "task_id": "test-123", "disposition": "completed",
        "duration_seconds": 42.0, "transcript": [], "events": [],
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
        "task_id": "test-456", "disposition": "completed",
        "duration_seconds": 10.0, "transcript": [], "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Cancel subscription", "--user-info", '{"name": "Alice", "account": "12345"}'])
    assert result.exit_code == 0
    call_kwargs = mock_run.call_args
    assert call_kwargs[1]["user_info"] == {"name": "Alice", "account": "12345"}


@patch("call_use.cli._run_call")
def test_dial_failed_returns_nonzero(mock_run):
    mock_run.return_value = {
        "task_id": "test-789", "disposition": "failed",
        "duration_seconds": 5.0, "transcript": [], "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 1


@patch("call_use.cli._run_call")
def test_dial_voicemail_returns_zero(mock_run):
    mock_run.return_value = {
        "task_id": "test-vm", "disposition": "voicemail",
        "duration_seconds": 15.0, "transcript": [], "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 0
    output = _extract_json(result.output)
    assert output["disposition"] == "voicemail"


@patch("call_use.cli._run_call")
def test_dial_no_answer_returns_zero(mock_run):
    mock_run.return_value = {
        "task_id": "test-na", "disposition": "no_answer",
        "duration_seconds": 30.0, "transcript": [], "events": [],
    }
    runner = CliRunner()
    result = runner.invoke(main, ["dial", "+18005551234", "--instructions", "Ask about hours"])
    assert result.exit_code == 0
