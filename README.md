# call-use

[![PyPI](https://img.shields.io/pypi/v/call-use)](https://pypi.org/project/call-use/)
[![Tests](https://github.com/agent-next/call-use/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-next/call-use/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25_(CI--enforced)-brightgreen)](https://github.com/agent-next/call-use/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://pypi.org/project/call-use/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Give your AI agent the ability to make real phone calls.**

call-use is an open-source outbound call-control runtime that lets AI agents dial real phones, navigate IVR menus, talk to humans, and return structured results. Think *browser-use*, but for phone calls.

> **Early release (v0.1)** — Core functionality works. API may change before v1.0. [Report issues](https://github.com/agent-next/call-use/issues).

<div align="center">

https://github.com/agent-next/call-use/raw/main/docs/assets/demo.mp4

</div>

```python
from call_use import CallAgent

outcome = await CallAgent(
    phone="+18001234567",
    instructions="Cancel my internet subscription",
    approval_required=False,
).call()

print(outcome.disposition)   # "completed"
print(outcome.transcript)    # [{speaker: "agent", text: "..."}, ...]
```

## Features

- **Four interfaces** — Python SDK, CLI, MCP server, and REST API. Use whichever fits your stack.
- **IVR navigation** — Navigate phone menus, press DTMF buttons, handle hold music automatically.
- **Human takeover** — Pause the AI mid-call, join as a human, then hand control back to the agent.
- **Approval flow** — Agent pauses and asks permission before taking sensitive actions.
- **Structured outcomes** — Every call returns typed results: transcript, events, disposition, duration.
- **Phone validation** — E.164 format enforcement, premium-rate blocking, Caribbean NPA blocking.
- **Framework integrations** — Works with [LangChain](examples/langchain_tool.py), [CrewAI](examples/crewai_integration.py), [OpenAI Agents](examples/openai_agents.py), and any MCP-compatible client.
- **Rate limiting** — Built-in per-key sliding window for the REST API.

## Installation

```bash
pip install call-use
```

## Quick Start

### Prerequisites

call-use connects four external services into a voice AI pipeline:

| Service | Purpose | Sign up |
|---------|---------|---------|
| [LiveKit](https://livekit.io/) | Real-time audio transport + agent dispatch | [Cloud](https://cloud.livekit.io/) or self-hosted |
| [Twilio](https://www.twilio.com/) | SIP trunk for PSTN connectivity | [Console](https://console.twilio.com/) |
| [Deepgram](https://deepgram.com/) | Speech-to-text | [Console](https://console.deepgram.com/) |
| [OpenAI](https://openai.com/) | LLM (GPT-4o) + text-to-speech | [Platform](https://platform.openai.com/) |

### Configuration

Set these environment variables (or use a `.env` file):

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL (`wss://...`) |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `SIP_TRUNK_ID` | Twilio SIP trunk ID configured in LiveKit |
| `DEEPGRAM_API_KEY` | Deepgram API key for STT |
| `OPENAI_API_KEY` | OpenAI API key for LLM + TTS |

### Start the worker

The worker process handles the actual voice pipeline:

```bash
call-use-worker start
```

### Make a call

**Python SDK:**

```python
import asyncio
from call_use import CallAgent

async def main():
    agent = CallAgent(
        phone="+18001234567",
        instructions="Ask about store hours",
        approval_required=False,
    )
    outcome = await agent.call()
    print(f"{outcome.disposition.value}: {outcome.duration_seconds:.0f}s")
    for t in outcome.transcript:
        print(f"  [{t['speaker']}] {t['text']}")

asyncio.run(main())
```

**CLI** — any agent that can run shell commands can make calls:

```bash
call-use dial "+18001234567" -i "Ask about store hours"
```

Events stream to stderr in real-time; structured JSON result goes to stdout.

**MCP Server** — native integration for Claude Code, Codex, and other MCP clients:

```json
{
  "mcpServers": {
    "call-use": {
      "command": "call-use-mcp",
      "env": {
        "LIVEKIT_URL": "wss://...",
        "LIVEKIT_API_KEY": "...",
        "LIVEKIT_API_SECRET": "...",
        "SIP_TRUNK_ID": "...",
        "DEEPGRAM_API_KEY": "your-deepgram-api-key",
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

Exposes four async tools: `dial` (returns immediately), `status`, `cancel`, `result`.

## Architecture

```
┌──────────┐         ┌──────────────┐         ┌────────────┐         ┌──────┐
│ Your Code│────────▶│ LiveKit Cloud│────────▶│ Twilio SIP │────────▶│ PSTN │
│ (SDK/CLI)│  gRPC   │              │  agent  │            │  SIP    │      │
└──────────┘         │  Room + Data │  dispatch            │         │ ☎    │
                     │   Channels   │         └────────────┘         └──────┘
                     └──────┬───────┘
                            │
                     ┌──────┴───────┐
                     │ call-use     │
                     │ worker       │
                     │              │
                     │ Deepgram STT │
                     │ GPT-4o LLM   │
                     │ OpenAI TTS   │
                     └──────────────┘
```

**Two processes:** your code dispatches a call task into a LiveKit room; the worker joins the room, dials via SIP, runs the voice conversation, and publishes the structured outcome.

## Human Takeover

Pause the AI agent, join the call yourself, then hand control back:

```python
call_task = asyncio.create_task(agent.call())

# ... when a human needs to take over:
token = await agent.takeover()   # returns LiveKit JWT
# ... join the room with the token, talk to the callee ...
await agent.resume()             # agent takes over again

result = await call_task
```

## Approval Flow

The agent pauses and asks before taking sensitive actions:

```python
agent = CallAgent(
    phone="+18001234567",
    instructions="Cancel my subscription. If they offer a discount, ask me first.",
    approval_required=True,
    on_approval=lambda data: "approved" if input(f"Approve '{data['details']}'? [y/n]: ").strip().lower() == "y" else "rejected",
)
```

## REST API

For multi-tenant deployments:

```python
from call_use import create_app
app = create_app(api_key="your-secret-key")
# uvicorn your_module:app
```

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/calls` | Create outbound call |
| `GET` | `/calls/{id}` | Get call status |
| `POST` | `/calls/{id}/inject` | Inject context into active call |
| `POST` | `/calls/{id}/takeover` | Human takeover |
| `POST` | `/calls/{id}/resume` | Resume AI agent |
| `POST` | `/calls/{id}/approve` | Approve pending action |
| `POST` | `/calls/{id}/reject` | Reject pending action |
| `POST` | `/calls/{id}/cancel` | Cancel call |

All endpoints require an `X-API-Key` header.

## Examples

| Example | Description |
|---------|-------------|
| [Customer service refund](examples/cs_refund_agent.py) | End-to-end refund automation |
| [Appointment scheduler](examples/appointment_scheduler.py) | Navigate IVR, book appointment |
| [Insurance claim](examples/insurance_claim.py) | File claim, capture claim number |
| [Subscription cancellation](examples/subscription_cancellation.py) | Handle retention offers via approval flow |
| [Multi-call workflow](examples/multi_call_workflow.py) | Chain sequential calls |
| [Webhook integration](examples/webhook_integration.py) | FastAPI + WebSocket events |
| [LangChain tool](examples/langchain_tool.py) | Use as a LangChain tool |
| [OpenAI Agents](examples/openai_agents.py) | OpenAI Agents SDK integration |
| [CrewAI](examples/crewai_integration.py) | PhoneCallTool for CrewAI |
| [Claude Code MCP](examples/claude_code_setup.md) | MCP server setup guide |

## Documentation

Full documentation at [docs.call-use.com](https://docs.call-use.com) — getting started, guides, API reference, and architecture deep-dive.

## Contributing

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
make check  # lint + typecheck + test (100% coverage) + build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `MissingEnvironmentError` on startup | One or more required env vars are unset | Ensure all six variables from the [Configuration](#configuration) table are exported (or present in your `.env` file). Run `call-use doctor` to check. |
| LiveKit connection failed / timeout | `LIVEKIT_URL` is wrong or the LiveKit server is unreachable | Verify `LIVEKIT_URL` starts with `wss://`, and that the LiveKit server (Cloud or self-hosted) is running and reachable from your network. |
| Worker not picking up calls | The worker process is not running | Start it with `call-use-worker start` in a separate terminal. |
| Call times out immediately | SIP trunk is misconfigured in LiveKit | Double-check `SIP_TRUNK_ID` matches an active Twilio SIP trunk in your LiveKit dashboard. Ensure the trunk's origination URI points to your LiveKit instance. |
| `PermissionError` writing log files | `~/.call-use/logs/` has restrictive permissions | Run `chmod 755 ~/.call-use/logs/` or set `CALL_USE_LOG_DIR` to a writable directory. |

## Known Limitations

- **In-memory state** — REST API call state is lost on restart; use LiveKit room metadata for recovery.
- **Single worker** — Horizontal scaling requires a shared state backend.
- **US/Canada only** — Outbound PSTN via Twilio SIP; international and inbound calling are planned.

## Legal Notice

call-use is a developer tool for legitimate business automation. Users are solely responsible for complying with all applicable telecommunications laws including TCPA, FCC regulations on AI-generated voices ([FCC 24-17](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal)), Do Not Call registry, and state recording consent laws. See [SECURITY.md](SECURITY.md) for details.

## License

[MIT](LICENSE)
