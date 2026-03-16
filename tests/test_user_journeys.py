"""User journey tests — test call-use from the user's perspective.

Every test simulates what a real user would do:
pip install call-use -> configure -> make call -> get result
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.bdd


# Mock livekit before any call_use imports that trigger SDK/server loading
for _mod in [
    "livekit",
    "livekit.api",
    "livekit.rtc",
    "livekit.protocol",
    "livekit.protocol.models",
    "dotenv",
]:
    sys.modules.setdefault(_mod, MagicMock())


class TestFirstTimeUser:
    """A new user installs call-use and tries to make a call."""

    def test_package_imports_without_livekit_running(self):
        """User does 'from call_use import CallAgent' — should not crash even without LiveKit."""
        from call_use import CallAgent, CallEvent, CallOutcome

        assert CallAgent is not None
        assert CallOutcome is not None
        assert CallEvent is not None

    def test_all_public_exports_importable(self):
        """User imports everything from __all__ — all should work."""
        from call_use import (
            CallAgent,
            CallError,
            CallErrorCode,
            CallEvent,
            CallEventType,
            CallOutcome,
            CallStateEnum,
            CallTask,
            DispositionEnum,
            create_app,
        )

        assert CallAgent is not None
        assert CallError is not None
        assert CallErrorCode is not None
        assert CallEvent is not None
        assert CallEventType is not None
        assert CallOutcome is not None
        assert CallStateEnum is not None
        assert CallTask is not None
        assert DispositionEnum is not None
        assert create_app is not None

    def test_version_accessible(self):
        """User checks version."""
        from call_use import __version__

        assert __version__  # version string is non-empty

    def test_cli_help_shows_usage(self):
        """User runs 'call-use --help'."""
        from click.testing import CliRunner

        from call_use.cli import main

        result = CliRunner().invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "call-use" in result.output
        assert "dial" in result.output

    def test_dial_help_shows_all_options(self):
        """User runs 'call-use dial --help' — should see all options."""
        from click.testing import CliRunner

        from call_use.cli import main

        result = CliRunner().invoke(main, ["dial", "--help"])
        assert result.exit_code == 0
        for opt in [
            "--instructions",
            "--user-info",
            "--caller-id",
            "--voice-id",
            "--timeout",
            "--approval-required",
        ]:
            assert opt in result.output

    def test_auth_command_removed_for_v01(self):
        """auth command removed for v0.1 — should not be registered."""
        from click.testing import CliRunner

        from call_use.cli import main

        result = CliRunner().invoke(main, ["auth", "--help"])
        assert result.exit_code != 0


class TestUserErrors:
    """User makes common mistakes — errors should be clear and actionable."""

    def test_dial_without_phone_shows_clear_error(self):
        """User forgets phone number."""
        from click.testing import CliRunner

        from call_use.cli import main

        result = CliRunner().invoke(main, ["dial"])
        assert result.exit_code != 0

    def test_dial_without_instructions_shows_clear_error(self):
        """User forgets --instructions."""
        from click.testing import CliRunner

        from call_use.cli import main

        result = CliRunner().invoke(main, ["dial", "+18001234567"])
        assert result.exit_code != 0

    def test_invalid_json_user_info_shows_clear_error(self):
        """User passes bad JSON in --user-info."""
        from click.testing import CliRunner

        from call_use.cli import main

        result = CliRunner().invoke(
            main, ["dial", "+18001234567", "-i", "test", "-u", "{bad json}"]
        )
        assert result.exit_code == 2

    def test_missing_env_vars_shows_what_to_set(self):
        """User hasn't configured .env — should see exactly what's missing."""
        from click.testing import CliRunner

        from call_use.cli import main

        with patch(
            "call_use.cli._run_call",
            side_effect=RuntimeError("Missing required environment variables:\n  LIVEKIT_URL"),
        ):
            result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
            assert "LIVEKIT_URL" in result.output

    def test_invalid_phone_number_rejected(self):
        """User passes invalid phone number to SDK."""
        from call_use.sdk import CallAgent

        with pytest.raises(ValueError):
            CallAgent(
                phone="not-a-number",
                instructions="test",
                approval_required=False,
            )

    def test_premium_number_rejected_with_explanation(self):
        """User tries to call 900 number."""
        from call_use.sdk import CallAgent

        with pytest.raises(ValueError, match="900"):
            CallAgent(
                phone="+19001234567",
                instructions="test",
                approval_required=False,
            )

    def test_approval_required_without_callback_rejected(self):
        """User sets approval_required=True but forgets on_approval."""
        from call_use.sdk import CallAgent

        with pytest.raises(ValueError, match="on_approval"):
            CallAgent(
                phone="+18001234567",
                instructions="test",
                approval_required=True,
            )


class TestCallOutcomeUsability:
    """User receives a CallOutcome and uses it."""

    def test_outcome_has_all_expected_fields(self):
        """User accesses outcome.disposition, .transcript, .events, .duration_seconds."""
        from call_use.models import CallOutcome, DispositionEnum

        outcome = CallOutcome(
            task_id="test-123",
            transcript=[
                {"speaker": "agent", "text": "Hello"},
                {"speaker": "callee", "text": "Hi"},
            ],
            events=[],
            duration_seconds=42.5,
            disposition=DispositionEnum.completed,
        )
        assert outcome.task_id == "test-123"
        assert outcome.disposition == DispositionEnum.completed
        assert outcome.duration_seconds == 42.5
        assert len(outcome.transcript) == 2
        assert outcome.transcript[0]["speaker"] == "agent"

    def test_outcome_serializes_to_json(self):
        """User converts outcome to JSON for storage/API response."""
        import json

        from call_use.models import CallOutcome, DispositionEnum

        outcome = CallOutcome(
            task_id="t1",
            transcript=[],
            events=[],
            duration_seconds=10.0,
            disposition=DispositionEnum.completed,
        )
        data = json.loads(outcome.model_dump_json())
        assert data["disposition"] == "completed"
        assert isinstance(data["duration_seconds"], float)

    def test_all_dispositions_accessible(self):
        """User checks all possible dispositions."""
        from call_use.models import DispositionEnum

        expected = {
            "completed",
            "failed",
            "no_answer",
            "busy",
            "voicemail",
            "timeout",
            "cancelled",
        }
        actual = {d.value for d in DispositionEnum}
        assert actual == expected


class TestCLIOutputFormat:
    """User parses CLI output in their automation scripts."""

    @patch("call_use.cli._run_call")
    def test_stdout_is_valid_json(self, mock_run):
        """User pipes stdout to jq — must be valid JSON."""
        import json

        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "completed",
            "duration_seconds": 30.0,
            "transcript": [{"speaker": "agent", "text": "Hi"}],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        # Extract JSON from output (may contain stderr too)
        lines = result.output.strip().split("\n")
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
        json_str = "\n".join(lines[json_start:])
        data = json.loads(json_str)
        assert "task_id" in data
        assert "disposition" in data
        assert "transcript" in data

    @patch("call_use.cli._run_call")
    def test_exit_code_0_for_completed(self, mock_run):
        """User gets exit code 0 when call completes successfully."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "completed",
            "duration_seconds": 10,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 0

    @patch("call_use.cli._run_call")
    def test_exit_code_0_for_voicemail(self, mock_run):
        """User gets exit code 0 when call reaches voicemail."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "voicemail",
            "duration_seconds": 10,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 0

    @patch("call_use.cli._run_call")
    def test_exit_code_1_for_failed(self, mock_run):
        """User gets exit code 1 when call fails."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "failed",
            "duration_seconds": 5,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 1

    @patch("call_use.cli._run_call")
    def test_exit_code_0_for_no_answer(self, mock_run):
        """User gets exit code 0 for no_answer (expected outcome)."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "no_answer",
            "duration_seconds": 30,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 0

    @patch("call_use.cli._run_call")
    def test_exit_code_0_for_busy(self, mock_run):
        """User gets exit code 0 for busy (expected outcome)."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "busy",
            "duration_seconds": 5,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 0

    @patch("call_use.cli._run_call")
    def test_exit_code_1_for_timeout(self, mock_run):
        """User gets exit code 1 for timeout (failure outcome)."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "timeout",
            "duration_seconds": 600,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 1

    @patch("call_use.cli._run_call")
    def test_exit_code_1_for_cancelled(self, mock_run):
        """User gets exit code 1 for cancelled (failure outcome)."""
        from click.testing import CliRunner

        from call_use.cli import main

        mock_run.return_value = {
            "task_id": "t1",
            "disposition": "cancelled",
            "duration_seconds": 15,
            "transcript": [],
            "events": [],
        }
        result = CliRunner().invoke(main, ["dial", "+18001234567", "-i", "test"])
        assert result.exit_code == 1


class TestMCPUserExperience:
    """User configures MCP in Claude Code and uses tools."""

    @pytest.mark.asyncio
    async def test_dial_returns_task_id_not_outcome(self):
        """User calls dial — should get task_id immediately, NOT full outcome."""
        import os

        from call_use.mcp_server import _do_dial

        with patch("call_use.mcp_server.LiveKitAPI") as MockAPI:
            mock_api = AsyncMock()
            mock_api.room.create_room.return_value = MagicMock()
            mock_api.agent_dispatch.create_dispatch.return_value = MagicMock()
            MockAPI.return_value.__aenter__ = AsyncMock(return_value=mock_api)
            MockAPI.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch.dict(
                os.environ,
                {
                    "LIVEKIT_URL": "wss://test",
                    "LIVEKIT_API_KEY": "k",
                    "LIVEKIT_API_SECRET": "s",
                    "SIP_TRUNK_ID": "ST_test",
                    "OPENAI_API_KEY": "sk-test",
                    "DEEPGRAM_API_KEY": "dg-test",
                },
            ):
                result = await _do_dial(phone="+12025551234", instructions="test")
                assert "task_id" in result
                assert result["status"] == "dispatched"
                assert "disposition" not in result  # NOT blocking

    @pytest.mark.asyncio
    async def test_dial_missing_env_returns_error_not_crash(self):
        """User hasn't configured keys — dial should return error JSON, not crash."""
        import os

        from call_use.mcp_server import _do_dial

        with patch.dict(os.environ, {}, clear=True):
            result = await _do_dial(phone="+18001234567", instructions="test")
            assert "error" in result


class TestRESTAPIUser:
    """User deploys call-use as a REST API service."""

    def test_create_app_requires_api_key(self):
        """User calls create_app() without API key — should get clear error."""
        import os

        from call_use.server import create_app

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="API_KEY"):
                create_app()

    def test_create_app_returns_fastapi_instance(self):
        """User creates app with API key — should get FastAPI app."""
        from call_use.server import create_app

        app = create_app(api_key="test-key")
        assert hasattr(app, "routes")
