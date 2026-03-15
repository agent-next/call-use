# call-use

[![PyPI](https://img.shields.io/pypi/v/call-use)](https://pypi.org/project/call-use/)
[![Tests](https://github.com/agent-next/call-use/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-next/call-use/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/agent-next/call-use/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://pypi.org/project/call-use/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Give your AI agent the ability to make phone calls.**

```python
from call_use import CallAgent

outcome = await CallAgent(
    phone="+18001234567",
    instructions="Cancel my internet subscription",
).call()

print(outcome.disposition)   # "completed"
print(outcome.transcript)    # [{speaker: "agent", text: "..."}, ...]
```

Open-source. Self-hostable. Works with any agent framework.

---

## Features

**4 interfaces** — use whichever fits your stack:

```bash
# Python SDK
outcome = await CallAgent(phone="+18001234567", instructions="...").call()

# CLI — any agent that runs bash can make calls
call-use dial "+18001234567" -i "Ask about store hours"

# MCP Server — native Claude Code / Codex integration
call-use-mcp  # stdio transport, 4 async tools

# REST API — multi-tenant deployments
curl -X POST localhost:8000/calls -H "X-API-Key: ..." -d '{"phone_number": "+18001234567"}'
```

**Built-in capabilities:**

| | |
|---|---|
| **IVR navigation** | Navigate phone menus, press buttons, handle hold music |
| **Human takeover** | Pause the agent mid-call, join as a human, hand back |
| **Approval flow** | Agent asks for permission before sensitive actions |
| **Structured outcomes** | Transcript, events, disposition, duration — all typed |
| **Phone validation** | Premium-rate blocking, Caribbean NPA blocking, E.164 |
| **Rate limiting** | Per-key sliding window for REST API |

## Quick start

```bash
pip install call-use
```

Configure environment ([full guide](https://docs.call-use.com/getting-started/configuration/)):

```bash
export LIVEKIT_URL="wss://..."          # LiveKit Cloud or self-hosted
export LIVEKIT_API_KEY="..."
export LIVEKIT_API_SECRET="..."
export SIP_TRUNK_ID="..."               # Twilio SIP trunk in LiveKit
export DEEPGRAM_API_KEY="..."           # STT
export OPENAI_API_KEY="..."             # LLM + TTS
```

Start the worker, then make a call:

```bash
call-use-worker start
```

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

## Human takeover

Pause the AI, join the call yourself, then hand back:

```python
token = await agent.takeover()   # returns LiveKit JWT
# ... join room with token, talk to callee ...
await agent.resume()             # agent takes over again
```

## Approval flow

Agent pauses and asks before sensitive actions:

```python
agent = CallAgent(
    phone="+18001234567",
    instructions="Cancel my subscription. If they offer a discount, ask me first.",
    approval_required=True,
    on_approval=lambda data: input(f"Approve '{data['details']}'? [y/n]: "),
)
```

## MCP Server

Native tool integration for Claude Code, Codex, and other MCP-compatible agents:

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
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

4 async tools: `dial` (returns immediately), `status`, `cancel`, `result`.

## REST API

```python
from call_use import create_app
app = create_app(api_key="your-secret-key")
# uvicorn your_module:app
```

| Method | Path | Description |
|--------|------|-------------|
| POST | `/calls` | Create outbound call |
| GET | `/calls/{id}` | Get status |
| POST | `/calls/{id}/inject` | Inject message into call |
| POST | `/calls/{id}/takeover` | Human takeover |
| POST | `/calls/{id}/resume` | Resume agent |
| POST | `/calls/{id}/approve` | Approve pending action |
| POST | `/calls/{id}/reject` | Reject pending action |
| POST | `/calls/{id}/cancel` | Cancel call |

All endpoints require `X-API-Key` header.

## Architecture

```
Your code ──▶ LiveKit Cloud ──▶ Twilio SIP ──▶ PSTN
                    │
              call-use worker
              (Deepgram STT + GPT-4o + OpenAI TTS)
```

Two processes: your code dispatches an agent into a LiveKit room; the worker joins, dials via SIP, runs the conversation, publishes the outcome.

## Examples

| Example | Description |
|---------|-------------|
| [Customer service refund](examples/cs_refund_agent.py) | End-to-end refund automation |
| [Appointment scheduler](examples/appointment_scheduler.py) | Navigate IVR, book appointment |
| [Insurance claim](examples/insurance_claim.py) | File claim, capture claim number |
| [Subscription cancellation](examples/subscription_cancellation.py) | Handle retention offers via approval |
| [Multi-call workflow](examples/multi_call_workflow.py) | Chain sequential calls |
| [Webhook integration](examples/webhook_integration.py) | FastAPI + WebSocket events |
| [LangChain tool](examples/langchain_tool.py) | Use as a LangChain tool |
| [OpenAI Agents](examples/openai_agents.py) | OpenAI Agents SDK integration |
| [CrewAI](examples/crewai_integration.py) | PhoneCallTool for CrewAI |
| [Claude Code MCP](examples/claude_code_setup.md) | MCP server setup guide |

## Documentation

Full docs at [docs.call-use.com](https://docs.call-use.com) — getting started, guides, API reference, architecture.

## Contributing

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
make check  # lint + typecheck + test (100% coverage) + build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Known Limitations

- **In-memory state** — REST API call state lost on restart
- **Caller ID** — Format validation only; ownership verification planned for v0.2
- **Single worker** — Horizontal scaling requires shared state backend
- **US/Canada only** — Outbound PSTN via Twilio SIP; international and inbound planned

## Legal Notice

call-use is a developer tool for legitimate business automation. Users are solely responsible for complying with all applicable telecommunications laws including TCPA, FCC regulations on AI-generated voices ([FCC 24-17](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal)), Do Not Call registry, and state recording consent laws. See [SECURITY.md](SECURITY.md) for details.

## License

MIT
