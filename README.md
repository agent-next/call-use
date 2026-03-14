# call-use

Open-source outbound call-control runtime for agent builders. Your AI agent dials a phone number, talks to a human, and reports back with a structured outcome.

```python
from call_use import CallAgent

agent = CallAgent(
    phone="+18001234567",
    instructions="Cancel my internet subscription. My account number is 12345.",
    on_event=lambda e: print(e),
    on_approval=lambda details: "approved",
)
outcome = await agent.call()

print(outcome.disposition)   # "completed"
print(outcome.transcript)    # [{"speaker": "callee", "text": "How can I help?"}, ...]
```

## What it does

- **Dials outbound** via Twilio SIP trunk through LiveKit
- **Talks** using Deepgram STT + OpenAI GPT-4o + GPT-4o-mini TTS
- **Reports** structured `CallOutcome` with transcript, events, and disposition
- **Human takeover** — pause the agent mid-call and take over the conversation
- **Approval flow** — agent asks for user approval before taking sensitive actions
- **REST API** — deploy as a service with `create_app()` for multi-tenant usage

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
- OpenAI API key (for LLM + TTS)
- Deepgram API key (for STT)

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
| `OPENAI_API_KEY` | OpenAI API key |
| `DEEPGRAM_API_KEY` | Deepgram API key |

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

## Development

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
pytest
```

## License

MIT
