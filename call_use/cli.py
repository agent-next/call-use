"""call-use CLI — agent-native interface for making outbound calls."""

import asyncio
import json
import os
import sys
from typing import Any

import click

from call_use.models import CallEvent


def _check_env():
    """Check required environment variables before attempting a call."""
    required = {
        "LIVEKIT_URL": "LiveKit server URL (wss://...)",
        "LIVEKIT_API_KEY": "LiveKit API key",
        "LIVEKIT_API_SECRET": "LiveKit API secret",
        "SIP_TRUNK_ID": "Twilio SIP trunk ID in LiveKit",
        "OPENAI_API_KEY": "OpenAI API key (for LLM reasoning and text-to-speech)",
        "DEEPGRAM_API_KEY": "Deepgram API key (for speech-to-text)",
    }
    missing = [f"  {k} — {v}" for k, v in required.items() if not os.environ.get(k)]
    if missing:
        msg = "Missing required environment variables:\n" + "\n".join(missing)
        msg += "\n\nSee: https://github.com/agent-next/call-use#configure"
        raise RuntimeError(msg)


def _event_printer(event: CallEvent):
    """Print events to stderr for real-time observability."""
    if event.type.value == "transcript":
        speaker = event.data.get("speaker", "?")
        text = event.data.get("text", "")
        click.echo(f"  [{speaker}] {text}", err=True)
    elif event.type.value == "state_change":
        new_state = event.data.get("to", "?")
        click.echo(f"  state: {new_state}", err=True)
    elif event.type.value == "approval_request":
        details = event.data.get("details", "")
        click.echo(f"  APPROVAL NEEDED: {details}", err=True)


def _stdin_approval_handler(data: dict) -> str:
    """Interactive approval handler — prompts user on stdin."""
    details = data.get("details", str(data)) if isinstance(data, dict) else str(data)
    click.echo(f"\n  APPROVAL NEEDED: {details}", err=True)
    response = click.prompt("  Approve? [y/n]", type=click.Choice(["y", "n"]), err=True)
    return "approved" if response == "y" else "rejected"


def _run_call(
    phone: str,
    instructions: str,
    user_info: dict | None = None,
    caller_id: str | None = None,
    voice_id: str | None = None,
    timeout: int = 600,
    approval_required: bool = False,
) -> dict:
    """Run a call synchronously via CallAgent. Returns outcome dict."""
    from dotenv import load_dotenv

    load_dotenv()
    _check_env()

    from call_use.sdk import CallAgent

    kwargs: dict[str, Any] = dict(
        phone=phone,
        instructions=instructions,
        user_info=user_info,
        caller_id=caller_id,
        voice_id=voice_id,
        approval_required=approval_required,
        timeout_seconds=timeout,
        on_event=_event_printer,
    )
    if approval_required:
        kwargs["on_approval"] = _stdin_approval_handler

    agent = CallAgent(**kwargs)
    outcome = asyncio.run(agent.call())
    return outcome.model_dump(mode="json")


@click.group()
@click.version_option(package_name="call-use")
def main():
    """call-use: give your AI agent the ability to make phone calls."""
    pass


@main.command()
@click.argument("phone")
@click.option("--instructions", "-i", required=True, help="What the agent should do on the call.")
@click.option("--user-info", "-u", default=None, help="JSON dict of context for the agent.")
@click.option("--caller-id", default=None, help="Outbound caller ID (E.164).")
@click.option(
    "--voice-id", default=None, help="TTS voice (alloy, echo, fable, onyx, nova, shimmer)."
)
@click.option("--timeout", default=600, type=int, help="Max call duration in seconds.")
@click.option(
    "--approval-required",
    is_flag=True,
    default=False,
    help="Require approval for sensitive actions.",
)
def dial(phone, instructions, user_info, caller_id, voice_id, timeout, approval_required):
    """Make an outbound phone call.

    PHONE: Target phone number in E.164 format (e.g., +18001234567)

    Events stream to stderr in real-time. Structured JSON result goes to stdout.

    \b
    Examples:
        call-use dial "+18001234567" -i "Ask about store hours"
        call-use dial "+18005551234" -i "Cancel subscription" -u '{"account": "12345"}'
    """
    parsed_user_info = None
    if user_info:
        try:
            parsed_user_info = json.loads(user_info)
        except json.JSONDecodeError:
            click.echo("Error: --user-info must be valid JSON", err=True)
            sys.exit(2)

    click.echo(f"Calling {phone}...", err=True)
    try:
        result = _run_call(
            phone=phone,
            instructions=instructions,
            user_info=parsed_user_info,
            caller_id=caller_id,
            voice_id=voice_id,
            timeout=timeout,
            approval_required=approval_required,
        )
    except ValueError as e:
        click.echo(f"Invalid phone number: {e}", err=True)
        sys.exit(2)
    except RuntimeError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except ConnectionError as e:
        click.echo(f"Could not connect to LiveKit: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(json.dumps(result, indent=2))

    disposition = result.get("disposition")
    expected_outcomes = {"completed", "voicemail", "no_answer", "busy"}
    if disposition not in expected_outcomes:
        sys.exit(1)


# ---------------------------------------------------------------------------
# doctor command
# ---------------------------------------------------------------------------

_DOCTOR_ENV_VARS = {
    "LIVEKIT_URL": "LiveKit server URL",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "SIP_TRUNK_ID": "Twilio SIP trunk ID in LiveKit",
    "OPENAI_API_KEY": "OpenAI API key",
    "DEEPGRAM_API_KEY": "Deepgram API key",
}


def _check_livekit_connectivity() -> tuple[bool, str]:
    """Try to list rooms on LiveKit. Returns (ok, message)."""
    try:
        from livekit.api import LiveKitAPI

        async def _probe():
            async with LiveKitAPI() as lkapi:
                await lkapi.room.list_rooms()

        asyncio.run(_probe())
        return True, "LiveKit connection OK"
    except Exception as e:
        return False, f"LiveKit connection failed: {e}"


@main.command()
def doctor():
    """Check your environment and connectivity for common issues."""
    from dotenv import load_dotenv

    load_dotenv()

    passed = 0
    failed = 0

    # 1. Environment variables
    for var, description in _DOCTOR_ENV_VARS.items():
        if os.environ.get(var):
            click.echo(click.style(f"  \u2713 {var} set", fg="green"))
            passed += 1
        else:
            click.echo(click.style(f"  \u2717 {var} missing", fg="red"))
            failed += 1

    # 2. LiveKit connectivity (only if URL + credentials are present)
    if all(os.environ.get(v) for v in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")):
        ok, msg = _check_livekit_connectivity()
        if ok:
            click.echo(click.style(f"  \u2713 {msg}", fg="green"))
            passed += 1
        else:
            click.echo(click.style(f"  \u2717 {msg}", fg="red"))
            failed += 1
    else:
        msg = "LiveKit connectivity skipped (missing credentials)"
        click.echo(click.style(f"  \u2717 {msg}", fg="red"))
        failed += 1

    # 3. Summary
    click.echo()
    click.echo(f"  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
