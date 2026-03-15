# Human Takeover

Human takeover lets you pause the AI agent mid-call, join the conversation as a human, and hand control back when you are done. This is useful when:

- The agent encounters a situation it cannot handle
- You want to verify something directly with the callee
- A sensitive part of the conversation requires human judgment

## How it works

1. You send a **takeover** command
2. The agent **mutes** its audio input and output (stops listening and speaking)
3. You receive a **LiveKit token** with publish permissions
4. You **join the room** with the token and talk directly to the callee
5. When done, you send a **resume** command with an optional summary
6. The agent **unmutes** and continues the conversation

The callee experiences no interruption -- they stay on the same call the entire time.

## SDK takeover

### Start a call and take over

```python
import asyncio
from call_use import CallAgent


async def main():
    agent = CallAgent(
        phone="+18001234567",
        instructions="Cancel my subscription",
        approval_required=False,
    )

    # Run the call in the background
    call_task = asyncio.create_task(agent.call())

    # Wait for the call to connect (poll events or use a delay)
    await asyncio.sleep(30)

    # Take over the call
    token = await agent.takeover()
    print(f"Takeover active. LiveKit token: {token[:20]}...")

    # The token is a LiveKit JWT with publish permissions.
    # Use it to join the room and talk to the callee.
    # (Join via LiveKit client SDK, web UI, or any WebRTC client)

    # When done, resume agent control
    await agent.resume()

    # Wait for the call to finish
    outcome = await call_task
    print(f"Disposition: {outcome.disposition.value}")


asyncio.run(main())
```

### Event-driven takeover

Use the event callback to decide when to take over:

```python
import asyncio
from call_use import CallAgent, CallEvent

takeover_signal = asyncio.Event()

def on_event(event: CallEvent):
    if event.type.value == "transcript":
        text = event.data.get("text", "").lower()
        # Take over if the agent seems stuck
        if "i need to check" in text or "one moment" in text:
            takeover_signal.set()

async def main():
    agent = CallAgent(
        phone="+18001234567",
        instructions="Negotiate a lower rate",
        approval_required=False,
        on_event=on_event,
    )

    call_task = asyncio.create_task(agent.call())

    # Wait for the takeover signal
    await takeover_signal.wait()
    token = await agent.takeover()

    # ... join and talk ...

    await agent.resume()
    outcome = await call_task
```

## REST API takeover

### Request takeover

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/takeover \
  -H "X-API-Key: your-key"
```

Response:

```json
{
  "status": "takeover_active",
  "takeover_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Resume agent control

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/resume \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"summary": "I confirmed the refund amount directly with the rep."}'
```

Response:

```json
{
  "status": "ai_resumed"
}
```

### Providing a summary

The `summary` field in the resume request gives the agent context about what happened during the takeover. The agent receives this as an internal operator note:

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/resume \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"summary": "The rep confirmed a $380 refund, processing in 5-7 business days. Continue with the rest of the task."}'
```

The agent will use this context naturally in the conversation without repeating it verbatim.

## State machine

During takeover, the call state transitions are:

```
connected -> human_takeover (on takeover command)
human_takeover -> connected (on resume command)
```

If the agent is in `awaiting_approval` state when takeover is requested, the pending approval is automatically cancelled:

```
awaiting_approval -> human_takeover (on takeover, cancels pending approval)
human_takeover -> connected (on resume)
```

## Using the LiveKit token

The takeover token is a standard LiveKit JWT with these permissions:

- `room_join: true` -- can join the room
- `can_subscribe: true` -- can hear the callee
- `can_publish: true` -- can speak to the callee
- `can_publish_data: false` -- cannot send data messages

You can use this token with:

- [LiveKit web client](https://docs.livekit.io/client-sdk/js/) -- join from a web browser
- [LiveKit Python SDK](https://docs.livekit.io/client-sdk/python/) -- join from Python
- [LiveKit mobile SDKs](https://docs.livekit.io/client-sdk/) -- join from mobile apps
- [LiveKit Meet](https://meet.livekit.io) -- paste the token to join

## Important notes

!!! warning "Agent mutes during takeover"
    During takeover, the agent's audio input and output are disabled. It cannot hear the callee or speak. Only you can communicate with the callee.

!!! note "No data channel access"
    The takeover token does not grant data channel publish permissions. You cannot send commands to the agent while in takeover mode -- use the resume endpoint to hand back control.

!!! tip "Keep takeovers brief"
    The call timeout continues to run during takeover. If you need more time, consider setting a longer `timeout_seconds` when creating the call.

## Next steps

- [Approval flow](approval-flow.md) -- approve actions without taking over
- [SDK guide](sdk.md) -- full SDK reference
- [REST API guide](rest-api.md) -- all endpoints
