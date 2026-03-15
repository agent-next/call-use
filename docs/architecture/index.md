# Architecture

call-use is a two-process architecture: a **dispatcher** (your code or the REST API) and a **worker** (the voice agent). They communicate through LiveKit rooms.

## System overview

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Your code   │────────>│  LiveKit      │────────>│  Twilio SIP  │
│  (CallAgent) │  room   │  Cloud/OSS    │  trunk  │  -> PSTN     │
└──────────────┘         └──────────────┘         └──────────────┘
                               │
                         ┌─────┴──────┐
                         │ call-use   │
                         │ worker     │
                         │ (Agent)    │
                         └────────────┘
```

### Two processes

1. **Dispatcher** (your code, REST API, CLI, or MCP server):
    - Creates a LiveKit room
    - Dispatches the call-use agent via LiveKit's agent dispatch API
    - Monitors the call via the LiveKit data channel
    - Receives the final `CallOutcome` from room metadata

2. **Worker** (`call-use-worker start`):
    - Listens for agent dispatch requests from LiveKit
    - Joins the room and dials the phone number via SIP
    - Runs the conversation with STT + LLM + TTS
    - Publishes events and outcome back to the room

## Data flow

```
[Your Code / REST API]
        │
        │ 1. Create room + dispatch agent
        │    (via LiveKit API)
        ▼
   [LiveKit Server]
        │
        │ 2. Agent dispatch notification
        ▼
  [call-use Worker]
        │
        │ 3. Dial phone via SIP
        ▼
   [Twilio SIP Trunk]
        │
        │ 4. PSTN call
        ▼
   [Phone / Callee]
        │
        │ 5. Audio stream (bidirectional)
        ▼
  [call-use Worker]
     │     │     │
     │     │     │ 6a. Speech-to-text (Deepgram Nova 3)
     │     │     │ 6b. LLM reasoning (GPT-4o)
     │     │     │ 6c. Text-to-speech (GPT-4o-mini TTS)
     │     │     │
     │     │     ▼
     │     │  [Audio response → Callee]
     │     │
     │     │ 7. Events published on data channel
     │     │    (topic: "call-events")
     │     ▼
     │  [Your Code receives events]
     │
     │ 8. Outcome written to room metadata
     ▼
  [Your Code reads outcome]
```

## Component stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Real-time infrastructure** | LiveKit Cloud or self-hosted | Room management, audio routing, agent dispatch |
| **SIP connectivity** | Twilio Elastic SIP Trunk | PSTN bridging via LiveKit SIP |
| **Speech-to-text** | Deepgram Nova 3 | Transcribe callee speech |
| **LLM** | OpenAI GPT-4o | Conversation reasoning, IVR navigation |
| **Text-to-speech** | OpenAI GPT-4o-mini TTS | Generate agent speech |
| **Voice activity detection** | Silero VAD | Detect speech vs. silence for turn-taking |
| **Noise cancellation** | LiveKit BVC Telephony | Clean up telephony audio |

## Agent state machine

The call-use worker agent implements a state machine that governs the call lifecycle:

```
                    ┌─────────┐
                    │ created │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │ dialing │
                    └────┬────┘
                         │
                    ┌────▼────┐        ┌────────────────┐
                    │connected│◄──────►│human_takeover   │
                    └────┬────┘        └────────────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
    ┌─────────▼──┐  ┌────▼────┐  ┌─▼──────────────┐
    │ in_ivr     │  │ on_hold │  │awaiting_approval│
    └─────────┬──┘  └────┬────┘  └─┬──────────────┘
              │          │          │
              └──────────┼──────────┘
                         │
                    ┌────▼────┐
                    │  ended  │
                    └─────────┘
```

### State descriptions

| State | Description |
|-------|-------------|
| `created` | CallTask created, not yet dispatched |
| `dialing` | SIP INVITE sent to Twilio, waiting for callee to answer |
| `ringing` | Phone is ringing at the callee's end |
| `connected` | Call connected, agent is actively conversing |
| `in_ivr` | Agent is navigating an automated phone menu (IVR) |
| `on_hold` | Agent has been placed on hold |
| `in_conversation` | Agent is speaking with a human representative |
| `awaiting_approval` | Agent paused, waiting for human approval of a sensitive action |
| `human_takeover` | Human has taken control of the call |
| `ended` | Call has terminated |

### Key transitions

- **Takeover**: From `connected` or `awaiting_approval` to `human_takeover`. If in `awaiting_approval`, the pending approval is cancelled.
- **Resume**: From `human_takeover` back to `connected`.
- **Approval**: From `connected` to `awaiting_approval` (when agent calls `request_user_approval`), then back to `connected` on approve/reject.
- **Cancel**: From any state to `ended`.
- **Timeout**: From any state to `ended` after `timeout_seconds`.

## Communication channels

### LiveKit data channel

call-use uses two data channel topics for communication:

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `call-events` | Worker -> Dispatcher | Event stream (transcript, state changes, approval requests, completion) |
| `backend-commands` | Dispatcher -> Worker | Control commands (takeover, resume, cancel, inject, approve, reject) |

### Room metadata

Room metadata is used for:

- **Agent identity**: The worker writes its participant identity to room metadata so the dispatcher knows where to send commands
- **Call state**: The worker updates room metadata with the current state (for polling-based interfaces like the REST API)
- **Outcome**: The worker writes the final `CallOutcome` to room metadata for retrieval after the call ends

## Concurrency model

The worker agent uses two locks to manage concurrent operations:

| Lock | Purpose | Behavior |
|------|---------|----------|
| `_cmd_lock` | Serializes state transitions | Short-held; prevents race conditions between commands |
| `_reply_lock` | Serializes `generate_reply` calls | Long-held; prevents overlapping LLM responses |

**Takeover special case**: Takeover calls `session.interrupt()` before acquiring `_cmd_lock`. This cancels any in-progress LLM response immediately, then acquires the lock for state transition.

## Evidence pipeline

The `EvidencePipeline` collects events and transcript entries throughout the call:

```
[Agent events] ──> EvidencePipeline ──> JSON log file (~/.call-use/logs/)
                        │
                        ├──> Data channel (call-events topic)
                        │
                        └──> CallOutcome (returned to dispatcher)
```

The pipeline:

1. Records all events internally
2. Notifies subscribers (which publish to the data channel)
3. On finalization, builds a `CallOutcome` and writes a JSON log file

## SIP error handling

The worker classifies SIP errors into dispositions using RFC 3261 status codes:

| SIP Code | Disposition |
|----------|-------------|
| 486 (Busy Here) | `busy` |
| 600 (Busy Everywhere) | `busy` |
| 480 (Temporarily Unavailable) | `no_answer` |
| 408 (Request Timeout) | `no_answer` |
| 487 (Request Terminated) | `cancelled` |
| Other | Falls back to string matching on error message |

## Security considerations

- **Phone validation**: Numbers are validated against E.164 NANP format with premium-rate and Caribbean number blocking
- **API authentication**: REST API requires X-API-Key header on all endpoints
- **Rate limiting**: Sliding-window per-key rate limiter prevents abuse
- **Injection defense**: Agent instructions include explicit defense against prompt injection from the callee
- **Sensitive data**: Agent is instructed to never share SSN, full credit card numbers, or passwords
- **Permission scoping**: LiveKit tokens are scoped to minimum necessary permissions (monitor = subscribe only, takeover = subscribe + publish)

## Next steps

- [Getting started](../getting-started/index.md) -- set up and make your first call
- [SDK guide](../guides/sdk.md) -- use the Python SDK
- [Models reference](../reference/models.md) -- data model details
- [Events reference](../reference/events.md) -- event types and payloads
