# Approval Flow

The approval flow lets the AI agent pause and ask for human sign-off before taking sensitive actions -- like accepting an offer, committing funds, or agreeing to terms. This gives you control over consequential decisions while letting the agent handle the conversation.

## How it works

1. The agent encounters a decision point (e.g., "We can refund $380")
2. The agent tells the callee "Let me check on that" and **mutes** its audio
3. The agent calls the `request_user_approval` tool with details
4. Your callback (SDK) or endpoint (REST API) receives the approval request
5. You return `"approved"` or `"rejected"`
6. The agent **unmutes** and continues based on your decision

## Enabling approval

### SDK

When `approval_required=True` (the default), you must provide an `on_approval` callback:

```python
from call_use import CallAgent


def on_approval(details: dict) -> str:
    """Called when the agent needs human approval.

    Args:
        details: Dict with 'approval_id' and 'details' keys.

    Returns:
        'approved' or 'rejected'
    """
    description = details.get("details", "")
    print(f"Agent wants to: {description}")

    response = input("Approve? (y/n): ").strip().lower()
    return "approved" if response == "y" else "rejected"


agent = CallAgent(
    phone="+18005551234",
    instructions="Call and negotiate a lower rate on my internet bill",
    user_info={"name": "Alice", "account_number": "12345"},
    approval_required=True,
    on_approval=on_approval,
)
```

### CLI

With `--approval-required`, the CLI prompts on stdin:

```bash
call-use dial "+18005551234" \
  -i "Negotiate a lower rate on my internet bill" \
  -u '{"name": "Alice", "account_number": "12345"}' \
  --approval-required
```

Output:

```
Calling +18005551234...
  state: connected
  [agent] Hi, I'm calling about my internet bill...
  [callee] The best rate I can offer is $49.99 per month.

  APPROVAL NEEDED: Accept rate of $49.99/month (down from $79.99)
  Approve? [y/n]: y

  [agent] That sounds great, I'll accept that offer.
  state: ended
```

### REST API

Use the `/approve` and `/reject` endpoints:

```bash
# Start a call with approval required
curl -X POST http://localhost:8000/calls \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+18005551234",
    "instructions": "Negotiate a lower rate",
    "approval_required": true
  }'

# When the agent requests approval, approve it
curl -X POST http://localhost:8000/calls/call-abcdefgh/approve \
  -H "X-API-Key: your-key"

# Or reject it
curl -X POST http://localhost:8000/calls/call-abcdefgh/reject \
  -H "X-API-Key: your-key"
```

## What triggers approval

The agent is instructed: "NEVER commit funds, accept offers, or agree to terms without calling the `request_user_approval` tool first." This applies to:

- Accepting a refund amount
- Agreeing to a new rate or plan
- Confirming a cancellation with fees
- Accepting contract terms
- Any financial commitment

The agent will naturally tell the callee something like "Let me check on that" or "I need to verify with my team" before pausing for approval.

## Approval details

The `on_approval` callback receives a dict with:

| Key | Type | Description |
|-----|------|-------------|
| `approval_id` | `str` | Unique ID for this approval request |
| `details` | `str` | Human-readable description of what the agent wants to do |

Example:

```python
{
    "approval_id": "apr-a1b2c3d4e5f6",
    "details": "Refund of $380.00, processing in 5-7 business days"
}
```

## Timeout behavior

If your approval callback does not respond within **60 seconds**, the approval is automatically **rejected**. The agent will continue the conversation as if the action was rejected.

!!! tip "Auto-approval"
    For automated workflows where you always want to approve, return `"approved"` immediately:
    ```python
    def auto_approve(details: dict) -> str:
        return "approved"
    ```

## State machine

During approval, the call state transitions are:

```
connected -> awaiting_approval (agent calls request_user_approval)
awaiting_approval -> connected (on approve or reject)
awaiting_approval -> human_takeover (if takeover during approval)
```

If you request a human takeover while an approval is pending, the pending approval is **cancelled** and the call transitions to `human_takeover`.

## Disabling approval

To disable the approval flow entirely, set `approval_required=False`:

```python
agent = CallAgent(
    phone="+18001234567",
    instructions="Ask about store hours",
    approval_required=False,  # Agent acts autonomously
)
```

!!! warning "No approval = autonomous agent"
    When `approval_required=False`, the agent will accept offers, agree to terms, and commit actions without asking. Only disable approval for low-stakes calls like information gathering.

## Complete example

```python
import asyncio
from call_use import CallAgent, CallEvent


def on_event(event: CallEvent):
    if event.type.value == "transcript":
        speaker = event.data.get("speaker", "?")
        text = event.data.get("text", "")
        print(f"  [{speaker}] {text}")
    elif event.type.value == "state_change":
        to_state = event.data.get("to", "?")
        print(f"  State: {to_state}")
    elif event.type.value == "approval_request":
        print(f"  [Approval requested via event]")
    elif event.type.value == "approval_response":
        result = event.data.get("result", "?")
        print(f"  [Approval {result}]")


def on_approval(details: dict) -> str:
    description = details.get("details", "Unknown action")
    print(f"\n  *** APPROVAL NEEDED ***")
    print(f"  Action: {description}")
    response = input("  Approve? (y/n): ").strip().lower()
    return "approved" if response == "y" else "rejected"


async def main():
    agent = CallAgent(
        phone="+18005551234",
        instructions="Get a refund for order #12345. The charge was $380.",
        user_info={
            "name": "Alice Smith",
            "order_number": "12345",
            "email": "alice@example.com",
        },
        approval_required=True,
        on_event=on_event,
        on_approval=on_approval,
    )

    outcome = await agent.call()
    print(f"\nDisposition: {outcome.disposition.value}")
    print(f"Duration: {outcome.duration_seconds:.1f}s")


asyncio.run(main())
```

## Next steps

- [Human takeover](human-takeover.md) -- take over the call entirely
- [SDK guide](sdk.md) -- full SDK reference
- [Events reference](../reference/events.md) -- all event types
