# Python SDK

The Python SDK is the most flexible way to use call-use. It gives you full control over the call lifecycle with async/await, real-time event streaming, human takeover, and approval flows.

## Basic usage

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
    print(outcome.disposition.value)  # "completed"

asyncio.run(main())
```

## CallAgent parameters

```python
agent = CallAgent(
    phone="+18001234567",           # Target number, E.164 NANP (required)
    instructions="Your task...",     # What the agent should do (required)
    user_info={"name": "Alice"},     # Context the agent can reference
    caller_id="+15551234567",        # Outbound caller ID (E.164 NANP)
    voice_id="alloy",               # TTS voice
    approval_required=True,          # Require approval for sensitive actions
    timeout_seconds=600,             # Max call duration (default: 600)
    on_event=my_event_handler,       # Real-time event callback
    on_approval=my_approval_handler, # Approval decision callback
    recording_disclaimer="This call may be recorded.",
)
```

### Parameter details

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `phone` | `str` | Yes | -- | Target phone number in E.164 NANP format (`+1XXXXXXXXXX`) |
| `instructions` | `str` | Yes | -- | What the agent should accomplish on the call |
| `user_info` | `dict` | No | `{}` | Key-value pairs the agent can reference (name, account number, etc.) |
| `caller_id` | `str` | No | `None` | Outbound caller ID in E.164 NANP format |
| `voice_id` | `str` | No | `"alloy"` | TTS voice: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` |
| `approval_required` | `bool` | No | `True` | Whether the agent must ask before sensitive actions |
| `timeout_seconds` | `int` | No | `600` | Maximum call duration in seconds |
| `on_event` | `Callable` | No | `None` | Callback for real-time events |
| `on_approval` | `Callable` | No | `None` | Callback for approval requests (required if `approval_required=True`) |
| `recording_disclaimer` | `str` | No | `None` | Spoken at the start of the call before the agent begins |

!!! note "Approval callback requirement"
    If `approval_required=True` (the default), you must provide an `on_approval` callback. If you don't need approval, set `approval_required=False`.

## Event streaming

Register an `on_event` callback to receive real-time events during the call:

```python
from call_use import CallEvent

def on_event(event: CallEvent):
    if event.type.value == "transcript":
        speaker = event.data.get("speaker", "?")
        text = event.data.get("text", "")
        print(f"[{speaker}] {text}")

    elif event.type.value == "state_change":
        old = event.data.get("from", "?")
        new = event.data.get("to", "?")
        print(f"State: {old} -> {new}")

    elif event.type.value == "dtmf":
        keys = event.data.get("keys", "")
        print(f"DTMF: {keys}")

    elif event.type.value == "approval_request":
        details = event.data.get("details", "")
        print(f"Approval needed: {details}")

    elif event.type.value == "call_complete":
        disposition = event.data.get("disposition", "?")
        print(f"Call complete: {disposition}")
```

!!! tip "Thread safety"
    The `on_event` callback runs in a thread pool executor, not the async event loop. It is safe to do blocking I/O (logging, HTTP requests, database writes) inside the callback.

## Human takeover

You can pause the AI agent mid-call and take over the conversation yourself:

```python
# Start the call
agent = CallAgent(
    phone="+18001234567",
    instructions="Cancel my subscription",
    approval_required=False,
)

# Run call in background
import asyncio
call_task = asyncio.create_task(agent.call())

# ... when you want to take over:
token = await agent.takeover()
# token is a LiveKit JWT — join the room with it to talk to the callee

# ... when done talking:
await agent.resume()

# Wait for call to finish
outcome = await call_task
```

The `takeover()` method:

1. Sends a takeover command to the agent
2. The agent mutes its audio input and output
3. Returns a LiveKit JWT token with publish permissions
4. You join the LiveKit room with that token and talk directly to the callee

The `resume()` method hands control back to the AI agent.

See the [Human Takeover guide](human-takeover.md) for a complete walkthrough.

## Approval flow

When `approval_required=True`, the agent will call your `on_approval` callback before taking sensitive actions (accepting offers, committing funds, agreeing to terms):

```python
def on_approval(details: dict) -> str:
    """Return 'approved' or 'rejected'."""
    print(f"Agent wants to: {details.get('details', '')}")
    response = input("Approve? (y/n): ").strip().lower()
    return "approved" if response == "y" else "rejected"

agent = CallAgent(
    phone="+18001234567",
    instructions="Negotiate a lower rate on my internet bill",
    approval_required=True,
    on_approval=on_approval,
)
```

The approval flow:

1. Agent encounters a decision point (e.g., "We can offer $49.99/month")
2. Agent tells the callee "Let me check on that" and mutes
3. Agent calls the `request_user_approval` tool
4. Your `on_approval` callback is invoked with the details
5. You return `"approved"` or `"rejected"`
6. Agent unmutes and continues the conversation based on your decision

!!! warning "Approval timeout"
    If your callback does not respond within 60 seconds, the approval is automatically rejected.

See the [Approval Flow guide](approval-flow.md) for more details.

## Cancelling a call

Cancel an in-progress call:

```python
await agent.cancel()
```

This sends a cancel command to the agent, which hangs up immediately. The call outcome will have `disposition="cancelled"`.

## Error handling

```python
try:
    outcome = await agent.call()
except ValueError as e:
    # Invalid phone number format
    print(f"Bad input: {e}")
except ConnectionError as e:
    # Cannot connect to LiveKit
    print(f"Connection error: {e}")
except RuntimeError as e:
    # Missing environment variables or other setup issues
    print(f"Setup error: {e}")
```

If the call connects but encounters issues, the error is reflected in the disposition rather than raised as an exception:

| Disposition | Meaning |
|-------------|---------|
| `completed` | Task finished successfully |
| `failed` | Connected but could not complete the task |
| `no_answer` | Nobody picked up |
| `busy` | Line was busy |
| `voicemail` | Reached voicemail |
| `timeout` | Exceeded `timeout_seconds` |
| `cancelled` | Cancelled via `agent.cancel()` |

## Phone number validation

call-use validates phone numbers before dialing:

- Must be E.164 NANP format: `+1` followed by 10 digits (e.g., `+18001234567`)
- Area code and exchange must start with 2-9
- Caribbean, Pacific, and non-geographic area codes are blocked
- Premium-rate numbers (900, 976) are blocked

Invalid numbers raise `ValueError` immediately.

## Complete example

```python
import asyncio
from call_use import CallAgent


def on_event(event):
    if event.type.value == "transcript":
        speaker = event.data.get("speaker", "?")
        text = event.data.get("text", "")
        print(f"  [{speaker}] {text}")
    elif event.type.value == "state_change":
        print(f"  State: {event.data.get('to')}")


def on_approval(details):
    print(f"\n  APPROVAL: {details.get('details', '')}")
    response = input("  Approve? (y/n): ").strip().lower()
    return "approved" if response == "y" else "rejected"


async def main():
    agent = CallAgent(
        phone="+18005551234",
        instructions="Cancel my internet subscription. My account number is in user_info.",
        user_info={
            "name": "Alice Smith",
            "account_number": "12345678",
        },
        voice_id="nova",
        approval_required=True,
        timeout_seconds=300,
        on_event=on_event,
        on_approval=on_approval,
        recording_disclaimer="This call may be recorded for quality purposes.",
    )

    print("Starting call...")
    outcome = await agent.call()

    print(f"\n--- Result ---")
    print(f"Disposition: {outcome.disposition.value}")
    print(f"Duration: {outcome.duration_seconds:.1f}s")
    for turn in outcome.transcript:
        print(f"  [{turn['speaker']}] {turn['text']}")


asyncio.run(main())
```

## Next steps

- [CLI guide](cli.md) -- use call-use from the command line
- [Human takeover](human-takeover.md) -- take over a call mid-conversation
- [Approval flow](approval-flow.md) -- approve sensitive actions
- [API reference](../reference/api.md) -- full class and method documentation
