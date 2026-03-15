"""Shared test fixtures for call-use tests.

LiveKit is not installed in the test environment. All livekit modules are mocked
at import time so that call_use.agent, call_use.sdk, and call_use.server can be
imported without the real LiveKit SDK.

This module-level setup runs before any test file is collected, ensuring the
mocks are in place when test modules do their own top-level imports.
"""

import sys
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Common livekit module mocks (shared across all test files)
# ---------------------------------------------------------------------------
# These are the base set of modules that every test file needs mocked.
# Individual test files may add additional module-specific mocks on top.

_COMMON_LIVEKIT_MODULES = [
    "livekit",
    "livekit.api",
    "livekit.rtc",
    "livekit.protocol",
    "livekit.protocol.sip",
    "livekit.protocol.models",
    "dotenv",
]

for _mod in _COMMON_LIVEKIT_MODULES:
    sys.modules.setdefault(_mod, MagicMock())


# ---------------------------------------------------------------------------
# Agent-specific mocks (needed by test_agent.py and test_agent_bdd.py)
# ---------------------------------------------------------------------------
# These additional modules are required when importing call_use.agent.

_AGENT_EXTRA_MODULES = [
    "livekit.agents",
    "livekit.agents.beta",
    "livekit.agents.beta.tools",
    "livekit.plugins",
    "livekit.plugins.openai",
    "livekit.plugins.deepgram",
    "livekit.plugins.silero",
    "livekit.plugins.noise_cancellation",
    "livekit.plugins.turn_detector",
    "livekit.plugins.turn_detector.multilingual",
]


class FakeAgent:
    """Minimal stand-in for livekit.agents.Agent.

    Provides the session property that _LiveKitCallAgent expects.
    """

    def __init__(self, *args, **kwargs):
        self._session = None

    @property
    def session(self):
        return self._session


class FakeAgentServer:
    """Minimal stand-in for livekit.agents.AgentServer.

    Provides rtc_session as a pass-through decorator so the original
    function body is preserved and can be tested directly.
    """

    def __init__(self, *args, **kwargs):
        pass

    def rtc_session(self, **kwargs):
        """Pass-through decorator that preserves the original function."""

        def decorator(fn):
            return fn

        return decorator


def _setup_agent_mocks():
    """Install agent-specific mocks. Called at module level."""
    _livekit_agents_mock = MagicMock()
    _livekit_agents_mock.Agent = FakeAgent
    _livekit_agents_mock.AgentServer = FakeAgentServer
    # function_tool must be callable -- return identity for non-decorator usage,
    # and also work as @function_tool decorator.
    _livekit_agents_mock.function_tool = lambda fn=None, **kw: fn if fn else (lambda f: f)

    for mod in _AGENT_EXTRA_MODULES:
        if mod == "livekit.agents":
            sys.modules.setdefault(mod, _livekit_agents_mock)
        else:
            sys.modules.setdefault(mod, MagicMock())


_setup_agent_mocks()


# ---------------------------------------------------------------------------
# Server-specific mocks (needed by test_server.py)
# ---------------------------------------------------------------------------


def _setup_server_mocks():
    """Install server-specific mocks on top of the base livekit mocks."""
    mock_livekit_api = MagicMock()
    mock_lkapi_instance = MagicMock()
    mock_lkapi_instance.__aenter__ = AsyncMock(return_value=mock_lkapi_instance)
    mock_lkapi_instance.__aexit__ = AsyncMock(return_value=None)
    mock_livekit_api.return_value = mock_lkapi_instance

    mock_lkapi_instance.agent_dispatch = MagicMock()
    mock_lkapi_instance.agent_dispatch.create_dispatch = AsyncMock()

    sys.modules["livekit.api"].LiveKitAPI = mock_livekit_api

    lk_api_mod = sys.modules["livekit"].api
    lk_api_mod.AccessToken = MagicMock
    lk_api_mod.VideoGrants = MagicMock
    lk_api_mod.CreateAgentDispatchRequest = MagicMock
    lk_api_mod.ListRoomsRequest = MagicMock
    lk_api_mod.ListParticipantsRequest = MagicMock
    lk_api_mod.SendDataRequest = MagicMock
    lk_api_mod.UpdateRoomMetadataRequest = MagicMock


_setup_server_mocks()
