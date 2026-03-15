# First Call

This tutorial walks you through making your first outbound phone call with call-use. By the end, you will have an AI agent that calls a phone number, completes a task, and returns a structured result.

## Before you begin

Make sure you have:

1. [Installed call-use](installation.md)
2. [Configured your environment](configuration.md) (`.env` file with all required variables)
3. Started the worker: `call-use-worker start`

## Step 1: Make a call with the CLI

The fastest way to test is with the CLI. Open a new terminal (keep the worker running in the other one):

```bash
call-use dial "+18001234567" -i "Ask what their business hours are"
```

Replace `+18001234567` with a real US/Canada phone number in E.164 format.

You will see real-time output on stderr:

```
Calling +18001234567...
  state: dialing
  state: connected
  [agent] Hi, I'm calling to ask about your business hours.
  [callee] Sure, we're open Monday through Friday, 9 AM to 5 PM.
  [agent] Thank you so much, that's all I needed. Have a great day!
  state: ended
```

And the structured JSON result on stdout:

```json
{
  "task_id": "task-a1b2c3d4",
  "disposition": "completed",
  "duration_seconds": 45.2,
  "transcript": [
    {"speaker": "agent", "text": "Hi, I'm calling to ask about your business hours."},
    {"speaker": "callee", "text": "Sure, we're open Monday through Friday, 9 AM to 5 PM."},
    {"speaker": "agent", "text": "Thank you so much, that's all I needed. Have a great day!"}
  ],
  "events": [...]
}
```

!!! tip "Pipe-friendly output"
    Events go to stderr, JSON goes to stdout. This means you can pipe the result to `jq` or another program:
    ```bash
    call-use dial "+18001234567" -i "Ask about hours" | jq '.disposition'
    ```

## Step 2: Make a call with Python

Create a file called `my_first_call.py`:

```python
import asyncio
from call_use import CallAgent


def on_event(event):
    """Print events as they happen."""
    if event.type.value == "transcript":
        speaker = event.data.get("speaker", "?")
        text = event.data.get("text", "")
        print(f"  [{speaker}] {text}")
    elif event.type.value == "state_change":
        print(f"  State: {event.data.get('to')}")


async def main():
    agent = CallAgent(
        phone="+18001234567",
        instructions="Ask what their business hours are",
        approval_required=False,
        on_event=on_event,
    )

    outcome = await agent.call()

    print(f"\nCall finished!")
    print(f"  Disposition: {outcome.disposition.value}")
    print(f"  Duration: {outcome.duration_seconds:.1f}s")
    print(f"  Transcript turns: {len(outcome.transcript)}")


asyncio.run(main())
```

Run it:

```bash
python my_first_call.py
```

## Step 3: Pass context to the agent

The agent can use context you provide. This is useful when calling on behalf of a user:

```python
agent = CallAgent(
    phone="+18005551234",
    instructions="Cancel my internet subscription",
    user_info={
        "name": "Alice Smith",
        "account_number": "12345678",
        "email": "alice@example.com",
    },
    approval_required=False,
    on_event=on_event,
)
```

The agent will use this information naturally when asked to verify identity or provide account details.

!!! warning "Sensitive information"
    The agent is instructed to never share SSNs, full credit card numbers, or passwords. Only pass information you are comfortable having the agent share with the call recipient.

## Step 4: Enable approval flow

For sensitive actions (accepting offers, committing funds), enable the approval flow:

```python
def on_approval(details):
    """Called when the agent needs human approval."""
    print(f"\n  APPROVAL NEEDED: {details.get('details', '')}")
    response = input("  Approve? (y/n): ").strip().lower()
    return "approved" if response == "y" else "rejected"


agent = CallAgent(
    phone="+18005551234",
    instructions="Negotiate a lower rate on my internet bill",
    user_info={"name": "Alice Smith", "account_number": "12345678"},
    approval_required=True,
    on_event=on_event,
    on_approval=on_approval,
)
```

When the agent encounters a decision point (e.g., "The best I can offer is $49.99/month"), it will pause and call your `on_approval` callback before proceeding.

## Understanding the result

Every call returns a `CallOutcome` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | Unique identifier for the call |
| `disposition` | `DispositionEnum` | How the call ended (see below) |
| `duration_seconds` | `float` | Total call duration |
| `transcript` | `list[dict]` | List of `{speaker, text, timestamp}` entries |
| `events` | `list[CallEvent]` | Full event log |
| `recording_url` | `str` or `None` | Recording URL if available |
| `metadata` | `dict` | Additional metadata (phone number, caller ID) |

### Disposition values

| Value | Meaning |
|-------|---------|
| `completed` | Task finished successfully |
| `failed` | Call connected but task could not be completed |
| `no_answer` | Nobody picked up |
| `busy` | Line was busy |
| `voicemail` | Reached voicemail |
| `timeout` | Call exceeded the timeout limit |
| `cancelled` | Call was cancelled by the caller |

## Next steps

- [:octicons-arrow-right-24: Python SDK deep dive](../guides/sdk.md) -- events, human takeover, advanced options
- [:octicons-arrow-right-24: CLI guide](../guides/cli.md) -- flags, piping, automation
- [:octicons-arrow-right-24: REST API guide](../guides/rest-api.md) -- deploy as a service
- [:octicons-arrow-right-24: MCP Server guide](../guides/mcp-server.md) -- integrate with Claude Code
