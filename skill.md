---
name: call-use
description: Make outbound phone calls via AI agent. Use when the user asks to call a phone number, cancel a subscription, get a refund, check store hours, or any task that requires talking to someone on the phone.
---

# call-use — Phone Calls for AI Agents

You have the ability to make outbound phone calls on behalf of the user.

## When to use

- User asks to call a business or person
- User wants to cancel a subscription, get a refund, check hours, make an appointment
- User needs to navigate a phone menu (IVR) or talk to customer service
- Any task that requires talking to someone on the phone

## How to use

### Option 1: MCP tools (preferred if available)

If call-use MCP server is configured, use these tools:

1. **`dial`** — Start a call (returns immediately with `task_id`)
   - `phone`: E.164 format (e.g., "+18001234567")
   - `instructions`: What to accomplish
   - `user_info`: Optional JSON with context (name, account number, etc.)

2. **`status`** — Check call progress
   - `task_id`: From the dial response

3. **`result`** — Get final outcome (transcript, disposition)
   - `task_id`: From the dial response

4. **`cancel`** — Stop an active call
   - `task_id`: From the dial response

**Workflow:**
```
dial → poll status every 10-15s → when state="ended" → get result
```

### Option 2: CLI

```bash
call-use dial "+18001234567" -i "Cancel my internet subscription" -u '{"name": "Alice", "account": "12345"}'
```

- JSON result goes to stdout (parse it)
- Events stream to stderr
- Exit 0 = success (completed, voicemail, no_answer, busy)
- Exit 1 = failure (failed, timeout, cancelled)

### Option 3: Python SDK

```python
from call_use import CallAgent

outcome = await CallAgent(
    phone="+18001234567",
    instructions="Cancel my internet subscription",
    user_info={"name": "Alice", "account": "12345"},
    approval_required=False,
).call()
```

## Important rules

1. **Always confirm the phone number and task with the user before calling**
2. **Never call emergency numbers (911) or premium rate numbers (900/976)**
3. **US/Canada numbers only** (E.164 format: +1XXXXXXXXXX)
4. **Be specific in instructions** — tell the agent exactly what to do, what info to provide
5. **Include user_info** when the agent needs to verify identity (name, account number, etc.)
6. **Set approval_required=True** for sensitive actions (refunds, cancellations involving money)

## Dispositions

| Disposition | Meaning |
|-------------|---------|
| `completed` | Task finished successfully |
| `voicemail` | Reached voicemail |
| `no_answer` | No one picked up |
| `busy` | Line was busy |
| `failed` | Call failed (wrong number, dropped, etc.) |
| `timeout` | Exceeded time limit |
| `cancelled` | Call was cancelled |

## Example conversation

User: "Call Comcast and cancel my internet. My account is 98765, name Alice Chen"

Agent thinking: User wants to cancel Comcast internet. I'll use call-use to make the call.

```bash
call-use dial "+18001234567" \
  -i "Cancel my internet subscription. Be firm but polite. Get confirmation number." \
  -u '{"name": "Alice Chen", "account_number": "98765"}'
```
