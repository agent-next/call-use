# Data Models

All data models are Pydantic v2 `BaseModel` subclasses defined in `call_use.models`.

## CallTask

Represents a call dispatch request with all parameters needed to make a call.

::: call_use.models.CallTask
    options:
      show_source: true

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `task_id` | `str` | Auto-generated | Unique task identifier (format: `task-XXXXXXXX`) |
| `phone_number` | `str` | (required) | Target phone number in E.164 NANP format |
| `caller_id` | `str \| None` | `None` | Outbound caller ID in E.164 NANP format |
| `instructions` | `str` | (required) | Task description for the agent |
| `user_info` | `dict` | `{}` | Key-value context for the agent |
| `voice_id` | `str \| None` | `None` | TTS voice identifier |
| `approval_required` | `bool` | `True` | Whether agent must get approval for sensitive actions |
| `timeout_seconds` | `int` | `600` | Maximum call duration in seconds |
| `recording_disclaimer` | `str \| None` | `None` | Disclaimer spoken at call start |

## CallOutcome

Structured result returned when a call completes.

::: call_use.models.CallOutcome
    options:
      show_source: true

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Unique task identifier |
| `transcript` | `list[dict]` | List of transcript entries: `{speaker, text, timestamp}` |
| `events` | `list[CallEvent]` | Complete list of call events |
| `duration_seconds` | `float` | Total call duration |
| `disposition` | `DispositionEnum` | How the call ended |
| `recording_url` | `str \| None` | Recording URL if available. Reserved for future use. Currently always `None`. |
| `metadata` | `dict` | Additional metadata (phone number, caller ID) |

### Transcript entry format

Each entry in the `transcript` list is a dict:

```python
{
    "speaker": "agent",       # "agent" or "callee"
    "text": "Hello, how...",  # Transcribed speech
    "timestamp": 1710000000.0 # Unix timestamp
}
```

## CallEvent

A single event emitted during a call.

::: call_use.models.CallEvent
    options:
      show_source: true

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timestamp` | `float` | Current time | Unix timestamp |
| `type` | `CallEventType` | (required) | Event type enum |
| `data` | `dict` | `{}` | Event-specific payload |

## CallError

Exception raised for call errors.

::: call_use.models.CallError
    options:
      show_source: true

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `code` | `CallErrorCode` | Error classification |
| `message` | `str` | Human-readable error message |

## Enums

### CallStateEnum

Call lifecycle states.

::: call_use.models.CallStateEnum
    options:
      show_source: true

| Value | Description |
|-------|-------------|
| `created` | Call task created, not yet dialing |
| `dialing` | SIP invite sent, waiting for answer |
| `ringing` | Phone is ringing (reserved — not currently emitted) |
| `connected` | Call connected, agent is active |
| `in_ivr` | Navigating an automated phone menu (reserved — not currently emitted) |
| `on_hold` | Placed on hold (reserved — not currently emitted) |
| `in_conversation` | Speaking with a human (reserved — not currently emitted) |
| `awaiting_approval` | Agent paused, waiting for human approval |
| `human_takeover` | Human has taken over the call |
| `ended` | Call has ended |

### DispositionEnum

How a call ended.

::: call_use.models.DispositionEnum
    options:
      show_source: true

| Value | Description |
|-------|-------------|
| `completed` | Task finished successfully, agent hung up normally |
| `failed` | Call connected but task could not be completed |
| `no_answer` | Nobody answered the phone |
| `busy` | Line was busy |
| `voicemail` | Reached voicemail |
| `timeout` | Call exceeded the timeout limit |
| `cancelled` | Call was cancelled |
| `error` | Internal error during call processing |

### CallEventType

Types of events emitted during a call.

::: call_use.models.CallEventType
    options:
      show_source: true

| Value | Description |
|-------|-------------|
| `state_change` | Call state transition |
| `transcript` | Speech transcript entry |
| `dtmf` | DTMF tone pressed |
| `approval_request` | Agent requested human approval |
| `approval_response` | Approval decision received |
| `takeover` | Human takeover initiated |
| `resume` | Agent control resumed |
| `error` | Error occurred |
| `call_complete` | Call finished with final outcome |

### CallErrorCode

Error classifications.

::: call_use.models.CallErrorCode
    options:
      show_source: true

| Value | Description |
|-------|-------------|
| `dial_failed` | Failed to place the SIP call |
| `no_answer` | No answer after ringing |
| `busy` | Line busy |
| `voicemail` | Reached voicemail |
| `mid_call_drop` | Call dropped unexpectedly |
| `timeout` | Call exceeded timeout |
| `provider_error` | SIP/Twilio provider error |
| `rate_limited` | Rate limit exceeded |
| `cancelled` | Call was cancelled |
| `worker_not_running` | No worker process available to handle the call |
| `configuration_error` | Required environment variables are missing |
