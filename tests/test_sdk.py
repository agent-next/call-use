"""Tests for call_use.sdk — Step 10 CallAgent SDK class."""

import sys
from unittest.mock import MagicMock

import pytest

# Mock livekit before import
for mod in [
    "livekit", "livekit.api", "livekit.rtc", "livekit.protocol",
    "livekit.protocol.models", "dotenv",
]:
    sys.modules.setdefault(mod, MagicMock())

from call_use.sdk import CallAgent


class TestCallAgentConstructor:
    def test_valid_inputs(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test task",
            on_approval=lambda d: "approved",
        )
        assert agent._phone == "+12025551234"
        assert agent._instructions == "Test task"

    def test_invalid_phone_raises(self):
        with pytest.raises(ValueError):
            CallAgent(
                phone="invalid",
                instructions="Test",
                on_approval=lambda d: "approved",
            )

    def test_invalid_caller_id_raises(self):
        with pytest.raises(ValueError):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                caller_id="bad-caller",
                on_approval=lambda d: "approved",
            )

    def test_approval_required_without_callback_raises(self):
        with pytest.raises(ValueError, match="on_approval"):
            CallAgent(
                phone="+12025551234",
                instructions="Test",
                approval_required=True,
                on_approval=None,
            )

    def test_approval_not_required_no_callback_ok(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            approval_required=False,
        )
        assert agent._approval_required is False

    def test_user_info_defaults_to_empty_dict(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            on_approval=lambda d: "approved",
        )
        assert agent._user_info == {}


class TestCallAgentCommands:
    async def test_send_command_raises_without_active_call(self):
        agent = CallAgent(
            phone="+12025551234",
            instructions="Test",
            on_approval=lambda d: "approved",
        )
        with pytest.raises(RuntimeError, match="No active call"):
            await agent._send_command("takeover")
