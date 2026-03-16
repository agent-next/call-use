"""call-use CLI \u2014 agent-native interface for making outbound calls."""

import asyncio
import json
import os
import sys
from typing import Any

import click

from call_use.models import CallError, CallErrorCode, CallEvent

_BASE_ENV_VARS = {
    "LIVEKIT_URL": "LiveKit server URL (wss://...)",
    "LIVEKIT_API_KEY": "LiveKit API key",
    "LIVEKIT_API_SECRET": "LiveKit API secret",
    "SIP_TRUNK_ID": "Twilio SIP trunk ID in LiveKit",
    "DEEPGRAM_API_KEY": "Deepgram API key (for speech-to-text)",
}

_PROVIDER_ENV_VARS: dict[str, dict[str, str]] = {
    "openai": {"OPENAI_API_KEY": "OpenAI API key (LLM + TTS)"},
    "openrouter": {
        "OPENROUTER_API_KEY": "OpenRouter API key (LLM)",
        "OPENAI_API_KEY": "OpenAI API key (for TTS)",
    },
    "google": {"GOOGLE_API_KEY": "Google API key (LLM + TTS)"},
    "grok": {
        "XAI_API_KEY": "xAI API key (LLM)",
        "OPENAI_API_KEY": "OpenAI API key (for TTS)",
    },
}


def _get_env_vars_for_provider(provider: str) -> dict[str, str]:
    """Return the full set of required env vars for the given LLM provider."""
    result = dict(_BASE_ENV_VARS)
    result.update(_PROVIDER_ENV_VARS.get(provider, _PROVIDER_ENV_VARS["openai"]))
    return result


def _check_env():
    """Check required environment variables before attempting a call."""
    provider = os.environ.get("CALL_USE_LLM_PROVIDER", "openai")
    required = _get_env_vars_for_provider(provider)
    missing = [f"  {k} \u2014 {v}" for k, v in required.items() if not os.environ.get(k)]
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
    """Interactive approval handler \u2014 prompts user on stdin."""
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
@click.option(
    "--timeout",
    default=600,
    type=click.IntRange(30, 3600),
    help="Max call duration in seconds (30-3600).",
)
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
    except CallError as e:
        if e.code == CallErrorCode.worker_not_running:
            click.echo(
                "Error: No worker available. "
                "Start the worker in another terminal:\n"
                "  call-use-worker start",
                err=True,
            )
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)
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


def _doctor_env_vars() -> dict[str, str]:
    """Return env vars the doctor command should check (provider-aware)."""
    provider = os.environ.get("CALL_USE_LLM_PROVIDER", "openai")
    return _get_env_vars_for_provider(provider)


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
    for var, description in _doctor_env_vars().items():
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


# ---------------------------------------------------------------------------
# setup command
# ---------------------------------------------------------------------------

_INFRA_KEYS: list[dict[str, object]] = [
    {
        "name": "LIVEKIT_URL",
        "hint": "wss://...",
        "hide": False,
        "validate": lambda v: v.startswith(("wss://", "ws://")),
        "error": "Must start with wss:// or ws://",
    },
    {"name": "LIVEKIT_API_KEY", "hint": None, "hide": False, "validate": None, "error": None},
    {"name": "LIVEKIT_API_SECRET", "hint": None, "hide": True, "validate": None, "error": None},
    {"name": "SIP_TRUNK_ID", "hint": None, "hide": False, "validate": None, "error": None},
]

_LLM_PROVIDERS: dict[str, dict[str, object]] = {
    "1": {
        "name": "OpenAI",
        "value": "openai",
        "keys": [
            {
                "name": "OPENAI_API_KEY",
                "hint": "LLM + TTS",
                "hide": True,
                "validate": lambda v: v.startswith("sk-"),
                "error": "Must start with sk-",
            },
        ],
    },
    "2": {
        "name": "OpenRouter",
        "value": "openrouter",
        "keys": [
            {
                "name": "OPENROUTER_API_KEY",
                "hint": "LLM",
                "hide": True,
                "validate": None,
                "error": None,
            },
            {
                "name": "OPENAI_API_KEY",
                "hint": "for TTS",
                "hide": True,
                "validate": lambda v: v.startswith("sk-"),
                "error": "Must start with sk-",
            },
        ],
    },
    "3": {
        "name": "Google Gemini",
        "value": "google",
        "keys": [
            {
                "name": "GOOGLE_API_KEY",
                "hint": "LLM + TTS",
                "hide": True,
                "validate": None,
                "error": None,
            },
        ],
    },
    "4": {
        "name": "Grok (xAI)",
        "value": "grok",
        "keys": [
            {
                "name": "XAI_API_KEY",
                "hint": "LLM",
                "hide": True,
                "validate": None,
                "error": None,
            },
            {
                "name": "OPENAI_API_KEY",
                "hint": "for TTS",
                "hide": True,
                "validate": lambda v: v.startswith("sk-"),
                "error": "Must start with sk-",
            },
        ],
    },
}

_STT_KEYS: list[dict[str, object]] = [
    {"name": "DEEPGRAM_API_KEY", "hint": None, "hide": True, "validate": None, "error": None},
]

_OPTIONAL_KEYS: list[dict[str, object]] = [
    {"name": "API_KEY", "hint": "for REST API auth", "hide": False},
]


def _prompt_key(key_def: dict[str, object], values: dict[str, str]) -> None:
    """Prompt for a single key, validate, and store in *values*."""
    name: str = key_def["name"]  # type: ignore[assignment]
    hint = f" ({key_def['hint']})" if key_def["hint"] else ""
    default = os.environ.get(name, "")
    prompt_text = f"  {name}{hint}"

    while True:
        prompt_display = f"  {name}{hint} [{default}]" if default else prompt_text
        value = click.prompt(
            prompt_display,
            default=default or "",
            hide_input=bool(key_def["hide"]),
            show_default=False,
        )
        value = value.strip()

        if not value:
            click.echo(click.style(f"  \u2717 {name} is required", fg="red"))
            continue

        validator = key_def["validate"]
        if validator and not validator(value):
            click.echo(click.style(f"  \u2717 {key_def['error']}", fg="red"))
            continue

        values[name] = value
        click.echo(click.style(f"  \u2713 {name}", fg="green"))
        click.echo()
        break


@main.command()
def setup():
    """Interactive first-time configuration wizard."""
    from pathlib import Path

    env_path = Path(".env")

    click.echo()
    click.echo(click.style("  call-use setup", bold=True) + " \u2014 first-time configuration")
    click.echo("  " + "\u2500" * 38)
    click.echo()
    click.echo("  This wizard will create a .env file with your API keys.")
    click.echo()

    # Check for existing .env
    if env_path.exists():
        overwrite = click.confirm("  Overwrite existing .env?", default=False)
        if not overwrite:
            click.echo("  Aborted.")
            return

    values: dict[str, str] = {}

    # --- Infrastructure keys ---
    _sep = "\u2500"
    click.echo(click.style(f"  {_sep * 3} Required {_sep * 28}", bold=True))
    click.echo()

    for key_def in _INFRA_KEYS:
        _prompt_key(key_def, values)

    # --- LLM provider selection ---
    click.echo("  LLM Provider:")
    for num, prov in _LLM_PROVIDERS.items():
        suffix = " (default)" if num == "1" else ""
        click.echo(f"    {num}. {prov['name']}{suffix}")

    choice = click.prompt("  Select", default="1")
    while choice not in _LLM_PROVIDERS:
        click.echo(click.style("  \u2717 Invalid choice", fg="red"))
        choice = click.prompt("  Select", default="1")

    provider = _LLM_PROVIDERS[choice]
    values["CALL_USE_LLM_PROVIDER"] = provider["value"]  # type: ignore[assignment]
    click.echo(click.style(f"  \u2713 {provider['name']}", fg="green"))
    click.echo()

    for key_def in provider["keys"]:  # type: ignore[union-attr]
        _prompt_key(key_def, values)  # type: ignore[arg-type]

    # --- STT key ---
    for key_def in _STT_KEYS:
        _prompt_key(key_def, values)

    # --- Optional keys ---
    click.echo(click.style(f"  {_sep * 3} Optional (press Enter to skip) {_sep * 5}", bold=True))
    click.echo()

    for key_def in _OPTIONAL_KEYS:
        name: str = key_def["name"]  # type: ignore[assignment]
        hint = f" ({key_def['hint']})" if key_def["hint"] else ""
        default = os.environ.get(name, "")
        prompt_text = f"  {name}{hint}"
        if default:
            prompt_text = f"  {name}{hint} [{default}]"

        value = click.prompt(
            prompt_text,
            default=default or "",
            hide_input=bool(key_def.get("hide", False)),
            show_default=False,
        )
        value = value.strip()

        if value:
            values[name] = value
            click.echo(click.style(f"  \u2713 {name}", fg="green"))
        else:
            click.echo(click.style(f"  \u23ed {name} skipped", fg="yellow"))
        click.echo()

    # --- Write .env ---
    click.echo(click.style(f"  {_sep * 3} Writing .env {_sep * 22}", bold=True))
    click.echo()

    lines = ["# Generated by call-use setup"] + [f"{k}={v}" for k, v in values.items()]
    env_path.write_text("\n".join(lines) + "\n")
    click.echo(click.style(f"  \u2713 Created .env with {len(values)} variables", fg="green"))
    click.echo()

    # --- Run doctor ---
    click.echo(click.style(f"  {_sep * 3} Verification {_sep * 20}", bold=True))
    click.echo()
    click.echo("  Running call-use doctor...")
    click.echo()

    from dotenv import load_dotenv

    load_dotenv(override=True)

    for var, _desc in _doctor_env_vars().items():
        if os.environ.get(var):
            click.echo(click.style(f"  \u2713 {var} set", fg="green"))
        else:
            click.echo(click.style(f"  \u2717 {var} missing", fg="red"))

    click.echo()
    click.echo('  Setup complete! Try: call-use dial "+18001234567" -i "Ask about store hours"')
