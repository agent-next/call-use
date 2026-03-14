# call-use

[![PyPI](https://img.shields.io/pypi/v/call-use)](https://pypi.org/project/call-use/)
[![Tests](https://github.com/agent-next/call-use/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-next/call-use/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/agent-next/call-use/blob/main/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://pypi.org/project/call-use/)

> **Give your AI agent the ability to make phone calls.** The [browser-use](https://github.com/browser-use/browser-use) for phones.

```python
from call_use import CallAgent

outcome = await CallAgent(phone="+18001234567", instructions="Cancel my subscription").call()
print(outcome.disposition)  # "completed"
```

## What it does

- **Dials outbound** via Twilio SIP trunk through LiveKit
- **Talks** using OpenAI Whisper STT + GPT-4o + GPT-4o-mini TTS
- **Reports** structured `CallOutcome` with transcript, events, and disposition
- **Human takeover** — pause the agent mid-call and take over the conversation
- **Approval flow** — agent asks for user approval before taking sensitive actions
- **REST API** — deploy as a service with `create_app()` for multi-tenant usage

## Why call-use?

| | call-use | Build from scratch | Pine AI |
|---|:---:|:---:|:---:|
| Make a phone call | 3 lines | months | sign up + $$$ |
| IVR navigation | built-in | weeks | built-in |
| Live transcript | built-in | weeks | built-in |
| Human takeover | built-in | weeks | — |
| Approval flow | built-in | days | — |
| Open source | yes | — | no |
| Self-hostable | yes | — | no |
| Any agent framework | yes | — | no |

## Works with

Claude Code · LangChain · OpenAI Agents · CrewAI · Any agent that runs bash

## Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Your code   │────────▶│  LiveKit      │────────▶│  Twilio SIP  │
│  (CallAgent) │  room   │  Cloud/OSS    │  trunk  │  → PSTN      │
└──────────────┘         └──────────────┘         └──────────────┘
                               │
                         ┌─────┴──────┐
                         │ call-use   │
                         │ worker     │
                         │ (Agent)    │
                         └────────────┘
```

Two processes:
1. **Your code** (or the REST API) creates a LiveKit room and dispatches an agent
2. **call-use worker** joins the room, dials via SIP, runs the conversation, and publishes the outcome

## Quick start

### Prerequisites

- Python 3.11+
- [LiveKit Cloud](https://livekit.io) or self-hosted LiveKit server
- Twilio SIP trunk connected to LiveKit
- OpenAI API key (for STT + LLM + TTS)

### Install

```bash
pip install call-use
```

### Configure

```bash
cp .env.example .env
# Fill in your keys
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL (`wss://...`) |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `SIP_TRUNK_ID` | Twilio SIP trunk ID in LiveKit |
| `OPENAI_API_KEY` | OpenAI API key (STT + LLM + TTS) |

### Run the worker

```bash
call-use-worker start
```

### Make a call

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
    print(f"Done: {outcome.disposition.value}")

asyncio.run(main())
```

## SDK usage

### CallAgent

```python
agent = CallAgent(
    phone="+18001234567",           # US/Canada number (required)
    instructions="Your task...",     # What the agent should do (required)
    user_info={"name": "Alice"},     # Info the agent can reference
    caller_id="+15551234567",        # Outbound caller ID
    voice_id="alloy",                # TTS voice (alloy/echo/fable/onyx/nova/shimmer)
    approval_required=True,          # Agent asks before sensitive actions
    timeout_seconds=600,             # Max call duration
    on_event=my_event_handler,       # Real-time event callback
    on_approval=my_approval_handler, # Approval decision callback
    recording_disclaimer="This call may be recorded.",
)
```

### Events

The `on_event` callback receives `CallEvent` objects:

| Event type | Description |
|------------|-------------|
| `state_change` | Call state changed (connected, human_takeover, etc.) |
| `transcript` | New speech transcript (speaker + text) |
| `dtmf` | DTMF tone detected |
| `approval_request` | Agent needs user approval |
| `call_complete` | Call finished with outcome |

### Human takeover

```python
# Pause agent, get token to join as human
token = await agent.takeover()
# ... join LiveKit room with token, talk to callee ...
await agent.resume()  # Hand back to agent
```

### CallOutcome

```python
outcome = await agent.call()
outcome.task_id          # Unique call identifier
outcome.disposition      # completed | failed | voicemail | no_answer | busy | timeout | cancelled
outcome.duration_seconds # Call duration
outcome.transcript       # List of {speaker, text} dicts
outcome.events           # List of CallEvent dicts
```

## CLI

Any agent that can run bash can make phone calls:

```bash
pip install call-use
call-use dial "+18001234567" -i "Ask about store hours"
```

Events stream to stderr, structured JSON result goes to stdout:

```bash
call-use dial "+18001234567" -i "Cancel subscription" -u '{"account": "12345"}'
# stdout: {"task_id": "...", "disposition": "completed", "transcript": [...]}
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

4 async tools: `dial` (non-blocking, returns task_id), `status`, `cancel`, `result`.

## REST API

For multi-tenant or server deployments:

```python
from call_use import create_app

app = create_app(api_key="your-secret-key")
# Run with: uvicorn your_module:app
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/calls` | Create a new outbound call |
| `GET` | `/calls/{id}` | Get call status and room state |
| `POST` | `/calls/{id}/inject` | Inject a message into the call |
| `POST` | `/calls/{id}/takeover` | Human takeover |
| `POST` | `/calls/{id}/resume` | Resume agent after takeover |
| `POST` | `/calls/{id}/approve` | Approve pending action |
| `POST` | `/calls/{id}/reject` | Reject pending action |
| `POST` | `/calls/{id}/cancel` | Cancel the call |

All endpoints require `X-API-Key` header.

## Examples

- [LangChain tool](https://github.com/agent-next/call-use/blob/main/examples/langchain_tool.py) — Use call-use as a LangChain tool
- [OpenAI Agents SDK](https://github.com/agent-next/call-use/blob/main/examples/openai_agents.py) — Integrate with OpenAI Agents
- [Claude Code MCP setup](https://github.com/agent-next/call-use/blob/main/examples/claude_code_setup.md) — Configure call-use as an MCP server
- [Customer service refund agent](https://github.com/agent-next/call-use/blob/main/examples/cs_refund_agent.py) — End-to-end refund automation
- [Skill](https://github.com/agent-next/call-use/blob/main/SKILL.md) — Claude Code / agent skill for automatic phone call capability

## Development

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
pytest
```

## License

MIT
