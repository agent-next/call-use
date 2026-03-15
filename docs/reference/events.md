# Events Reference

call-use emits structured events throughout the call lifecycle. Events are delivered in real time via the `on_event` callback (SDK), the `call-events` LiveKit data channel (REST API), or the evidence pipeline logs.

## Event structure

Every event is a `CallEvent` with three fields:

```python
class CallEvent(BaseModel):
    timestamp: float    # Unix timestamp
    type: CallEventType # Event type enum
    data: dict          # Event-specific payload
```

## Event types

### state_change

Emitted when the call state transitions.

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `from` | `str` | Previous state |
| `to` | `str` | New state |

**Example:**

```json
{
  "timestamp": 1710000000.0,
  "type": "state_change",
  "data": {
    "from": "dialing",
    "to": "connected"
  }
}
```

**Possible state transitions:**

```
created -> dialing -> ringing -> connected
connected -> in_ivr -> connected
connected -> on_hold -> connected
connected -> awaiting_approval -> connected
connected -> human_takeover -> connected
connected -> ended
awaiting_approval -> human_takeover -> connected
any state -> ended
```

### transcript

Emitted when speech is transcribed (either agent or callee).

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `speaker` | `str` | `"agent"` or `"callee"` |
| `text` | `str` | Transcribed speech |
| `timestamp` | `float` | Unix timestamp of the speech |

**Example:**

```json
{
  "timestamp": 1710000005.0,
  "type": "transcript",
  "data": {
    "speaker": "callee",
    "text": "Thank you for calling. How can I help you?",
    "timestamp": 1710000005.0
  }
}
```

### dtmf

Emitted when the agent presses DTMF keys (phone keypad tones) during IVR navigation.

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `keys` | `str` | DTMF keys pressed (e.g., `"1"`, `"0"`, `"1234"`) |

**Example:**

```json
{
  "timestamp": 1710000010.0,
  "type": "dtmf",
  "data": {
    "keys": "1"
  }
}
```

### approval_request

Emitted when the agent requests human approval before a sensitive action.

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `approval_id` | `str` | Unique approval request ID |
| `details` | `str` | Human-readable description of the proposed action |
| `agent_identity` | `str` | LiveKit identity of the agent (internal) |

**Example:**

```json
{
  "timestamp": 1710000020.0,
  "type": "approval_request",
  "data": {
    "approval_id": "apr-a1b2c3d4e5f6",
    "details": "Accept refund of $380.00, processed in 5-7 business days",
    "agent_identity": "agent-task-a1b2"
  }
}
```

### approval_response

Emitted when an approval decision is received.

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `approval_id` | `str` | The approval request ID |
| `result` | `str` | `"approved"`, `"rejected"`, or `"cancelled"` |

**Example:**

```json
{
  "timestamp": 1710000025.0,
  "type": "approval_response",
  "data": {
    "approval_id": "apr-a1b2c3d4e5f6",
    "result": "approved"
  }
}
```

### takeover

Emitted when a human takeover is initiated.

**Payload:** Empty dict `{}`

**Example:**

```json
{
  "timestamp": 1710000030.0,
  "type": "takeover",
  "data": {}
}
```

### resume

Emitted when agent control is resumed after a human takeover.

**Payload:** Empty dict `{}`

**Example:**

```json
{
  "timestamp": 1710000060.0,
  "type": "resume",
  "data": {}
}
```

### error

Emitted when an error occurs during the call.

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `code` | `str` | Error code (see `CallErrorCode` enum) |
| `message` | `str` | Human-readable error description |

**Example:**

```json
{
  "timestamp": 1710000005.0,
  "type": "error",
  "data": {
    "code": "dial_failed",
    "message": "SIP 486 Busy Here"
  }
}
```

**Error codes:**

| Code | Description |
|------|-------------|
| `dial_failed` | Failed to place the SIP call |
| `no_answer` | No answer after ringing |
| `busy` | Line busy |
| `voicemail` | Reached voicemail |
| `mid_call_drop` | Call dropped unexpectedly during conversation |
| `timeout` | Call exceeded timeout |
| `provider_error` | SIP/Twilio provider error |
| `rate_limited` | Rate limit exceeded |
| `cancelled` | Call was cancelled |

### call_complete

Emitted when the call finishes. Contains the full `CallOutcome`.

**Payload:**

| Key | Type | Description |
|-----|------|-------------|
| `task_id` | `str` | Unique task identifier |
| `transcript` | `list[dict]` | Full transcript |
| `events` | `list[dict]` | All events (serialized) |
| `duration_seconds` | `float` | Total call duration |
| `disposition` | `str` | How the call ended |
| `recording_url` | `str \| null` | Recording URL if available |
| `metadata` | `dict` | Additional metadata |

**Example:**

```json
{
  "timestamp": 1710000045.0,
  "type": "call_complete",
  "data": {
    "task_id": "task-a1b2c3d4",
    "transcript": [
      {"speaker": "agent", "text": "Hello, I'm calling about...", "timestamp": 1710000005.0}
    ],
    "events": [...],
    "duration_seconds": 40.0,
    "disposition": "completed",
    "recording_url": null,
    "metadata": {"phone_number": "+18001234567", "caller_id": null}
  }
}
```

## Receiving events

### Python SDK

Use the `on_event` callback:

```python
from call_use import CallAgent, CallEvent

def on_event(event: CallEvent):
    print(f"{event.type.value}: {event.data}")

agent = CallAgent(
    phone="+18001234567",
    instructions="Ask about hours",
    approval_required=False,
    on_event=on_event,
)
```

### LiveKit data channel

Subscribe to the `call-events` topic in the LiveKit room:

```python
from livekit import rtc
import json

room = rtc.Room()

@room.on("data_received")
def on_data(dp):
    if dp.topic == "call-events":
        event = json.loads(dp.data.decode())
        print(event)

await room.connect(LIVEKIT_URL, monitor_token)
```

### Evidence logs

Events are also written to JSON files at `~/.call-use/logs/{task_id}.json` (configurable via `CALL_USE_LOG_DIR`).

## Next steps

- [Models reference](models.md) -- full data model documentation
- [SDK guide](../guides/sdk.md) -- event handling patterns
- [Architecture](../architecture/index.md) -- how events flow through the system
