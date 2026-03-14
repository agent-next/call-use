"""call-use: Open-source outbound call-control runtime for agent builders."""

from call_use._version import __version__
from call_use.models import (
    CallError,
    CallErrorCode,
    CallEvent,
    CallEventType,
    CallOutcome,
    CallStateEnum,
    CallTask,
    DispositionEnum,
)

__all__ = [
    "__version__",
    "CallAgent",
    "CallError",
    "CallErrorCode",
    "CallEvent",
    "CallEventType",
    "CallOutcome",
    "CallStateEnum",
    "CallTask",
    "DispositionEnum",
    "create_app",
    "mcp_server",
]


def __getattr__(name: str):
    """Lazy imports for modules that require livekit."""
    if name == "CallAgent":
        from call_use.sdk import CallAgent
        return CallAgent
    if name == "create_app":
        from call_use.server import create_app
        return create_app
    if name == "mcp_server":
        import call_use.mcp_server
        return call_use.mcp_server
    raise AttributeError(f"module 'call_use' has no attribute {name!r}")
