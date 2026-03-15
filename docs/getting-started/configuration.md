# Configuration

call-use requires credentials for LiveKit, Twilio, Deepgram, and OpenAI. All configuration is done through environment variables.

## Environment variables

Create a `.env` file in your project root (call-use loads it automatically via `python-dotenv`):

```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Twilio SIP trunk (configured in LiveKit)
SIP_TRUNK_ID=ST_xxxxxxxxxxxxxxxxxxxxxxxx

# Deepgram (speech-to-text)
DEEPGRAM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI (LLM + TTS)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Required variables

| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `LIVEKIT_URL` | LiveKit server URL (`wss://...`) | [LiveKit Cloud dashboard](https://cloud.livekit.io) or your self-hosted server |
| `LIVEKIT_API_KEY` | LiveKit API key | LiveKit Cloud dashboard > Settings > Keys |
| `LIVEKIT_API_SECRET` | LiveKit API secret | Generated with the API key |
| `SIP_TRUNK_ID` | SIP trunk ID in LiveKit | LiveKit dashboard > SIP > Trunks (after connecting Twilio) |
| `DEEPGRAM_API_KEY` | Deepgram API key | [Deepgram console](https://console.deepgram.com) |
| `OPENAI_API_KEY` | OpenAI API key | [OpenAI platform](https://platform.openai.com/api-keys) |

### Optional variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | (none) | API key for REST API authentication |
| `RATE_LIMIT_MAX` | `10` | Maximum calls per rate limit window |
| `RATE_LIMIT_WINDOW` | `3600` | Rate limit window in seconds |
| `CALL_USE_LOG_DIR` | `~/.call-use/logs` | Directory for call evidence logs |

## Setting up LiveKit

1. **Create a LiveKit Cloud account** at [livekit.io](https://livekit.io) (or deploy self-hosted)
2. **Create a new project** in the dashboard
3. **Copy your credentials**: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

## Setting up Twilio SIP

1. **Create a Twilio account** at [twilio.com](https://twilio.com)
2. **Buy a phone number** (this becomes your outbound caller ID)
3. **Create an Elastic SIP trunk** in Twilio
4. **Connect the trunk to LiveKit** following the [LiveKit SIP guide](https://docs.livekit.io/agents/quickstarts/outbound-calls/)
5. **Copy the SIP Trunk ID** from LiveKit dashboard > SIP > Trunks

!!! tip "LiveKit SIP setup guide"
    The LiveKit documentation has a detailed walkthrough for connecting Twilio SIP trunks: [docs.livekit.io/agents/quickstarts/outbound-calls](https://docs.livekit.io/agents/quickstarts/outbound-calls/)

## Setting up Deepgram

1. **Create a Deepgram account** at [deepgram.com](https://deepgram.com)
2. **Create an API key** in the [Deepgram console](https://console.deepgram.com)
3. call-use uses the **Nova 3** model with English (US) language

## Setting up OpenAI

1. **Create an OpenAI account** at [platform.openai.com](https://platform.openai.com)
2. **Create an API key** at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
3. call-use uses **GPT-4o** for the LLM and **GPT-4o-mini TTS** for speech synthesis

## Verifying your configuration

The CLI checks for required environment variables before making a call. Run a quick check:

```bash
call-use dial "+18001234567" -i "Test" 2>&1 | head -5
```

If any variables are missing, you will see a clear error message listing what is needed:

```
Missing required environment variables:
  LIVEKIT_URL — LiveKit server URL (wss://...)
  SIP_TRUNK_ID — Twilio SIP trunk ID in LiveKit
```

## Starting the worker

Before making calls, start the call-use worker process in a separate terminal:

```bash
call-use-worker start
```

The worker connects to LiveKit and waits for call dispatch requests. Keep it running while you make calls.

!!! warning "Worker must be running"
    The worker process is required for all interfaces (SDK, CLI, REST API, MCP). If the worker is not running, calls will time out waiting for an agent to join the room.

## Next steps

[:octicons-arrow-right-24: Make your first call](first-call.md)
