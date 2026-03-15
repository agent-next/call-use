# REST API

The REST API lets you deploy call-use as a service for multi-tenant or server-side usage. It is built with FastAPI and provides 8 endpoints for full call lifecycle management.

## Quick start

### Create the server

```python
# server.py
from call_use import create_app

app = create_app(api_key="your-secret-key")
```

### Run with Uvicorn

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

!!! note "Worker required"
    The REST API dispatches calls to the call-use worker. Make sure `call-use-worker start` is running in a separate process.

## Authentication

All endpoints require the `X-API-Key` header:

```bash
curl -X POST http://localhost:8000/calls \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+18001234567", "instructions": "Ask about hours"}'
```

The API key is set when creating the app via `create_app(api_key="...")` or through the `API_KEY` environment variable.

## Endpoints

### POST /calls

Create a new outbound call.

**Request body:**

```json
{
  "phone_number": "+18001234567",
  "instructions": "Cancel my internet subscription",
  "caller_id": "+15551234567",
  "user_info": {"name": "Alice", "account": "12345"},
  "voice_id": "alloy",
  "approval_required": true,
  "timeout_seconds": 600,
  "recording_disclaimer": "This call may be recorded."
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `phone_number` | `str` | Yes | -- | Target number in E.164 NANP format |
| `instructions` | `str` | No | `"Have a friendly conversation"` | Task for the agent |
| `caller_id` | `str` | No | `null` | Outbound caller ID (E.164 NANP) |
| `user_info` | `dict` | No | `{}` | Context for the agent |
| `voice_id` | `str` | No | `null` | TTS voice |
| `approval_required` | `bool` | No | `true` | Require approval for sensitive actions |
| `timeout_seconds` | `int` | No | `600` | Max call duration |
| `recording_disclaimer` | `str` | No | `null` | Spoken disclaimer at call start |

**Response (201):**

```json
{
  "task_id": "call-abcdefgh",
  "status": "dialing",
  "room_name": "call-abcdefgh",
  "livekit_token": "eyJ..."
}
```

The `livekit_token` is a subscribe-only monitor token. Use it to join the LiveKit room and receive real-time events.

**curl example:**

```bash
curl -X POST http://localhost:8000/calls \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+18001234567",
    "instructions": "Ask about store hours",
    "approval_required": false
  }'
```

---

### GET /calls/{call_id}

Get the current status of a call.

**Response:**

```json
{
  "task_id": "call-abcdefgh",
  "state": "connected",
  "participants": ["agent-call-abc", "phone-callee"]
}
```

**curl example:**

```bash
curl http://localhost:8000/calls/call-abcdefgh \
  -H "X-API-Key: your-secret-key"
```

---

### POST /calls/{call_id}/inject

Inject a message into an active call. The agent receives it as an internal operator note and uses the information naturally in conversation (without repeating it verbatim).

**Request body:**

```json
{
  "message": "The customer's preferred callback number is +15551234567"
}
```

**Response:**

```json
{
  "status": "sent"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/inject \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Offer them a 20% discount if they ask about pricing"}'
```

---

### POST /calls/{call_id}/takeover

Request human takeover of a call. The agent mutes and you receive a token with publish permissions to join and talk.

**Response:**

```json
{
  "status": "takeover_active",
  "takeover_token": "eyJ..."
}
```

The `takeover_token` is a LiveKit JWT with audio publish permissions. Use it to join the room and speak directly to the callee.

**curl example:**

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/takeover \
  -H "X-API-Key: your-secret-key"
```

!!! note "Takeover timeout"
    The endpoint polls for the agent to acknowledge the takeover. If the agent does not respond within 2 seconds, the request returns HTTP 504.

---

### POST /calls/{call_id}/resume

Resume agent control after a human takeover.

**Request body:**

```json
{
  "summary": "I confirmed the refund amount with the customer directly."
}
```

The `summary` field is optional. If provided, it is passed to the agent as context about what happened during the human takeover.

**Response:**

```json
{
  "status": "ai_resumed"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/resume \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"summary": "Confirmed the refund amount."}'
```

---

### POST /calls/{call_id}/approve

Approve a pending action requested by the agent.

**Response:**

```json
{
  "status": "sent_approve",
  "approval_id": "apr-abc123def456"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/approve \
  -H "X-API-Key: your-secret-key"
```

---

### POST /calls/{call_id}/reject

Reject a pending action requested by the agent.

**Response:**

```json
{
  "status": "sent_reject",
  "approval_id": "apr-abc123def456"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/reject \
  -H "X-API-Key: your-secret-key"
```

---

### POST /calls/{call_id}/cancel

Cancel an active call. The agent hangs up immediately.

**Response:**

```json
{
  "status": "cancelling",
  "call_id": "call-abcdefgh"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/calls/call-abcdefgh/cancel \
  -H "X-API-Key: your-secret-key"
```

## Rate limiting

The REST API includes a sliding-window rate limiter per API key.

| Setting | Default | Environment Variable |
|---------|---------|---------------------|
| Max calls per window | 10 | `RATE_LIMIT_MAX` |
| Window duration (seconds) | 3600 | `RATE_LIMIT_WINDOW` |

When the limit is exceeded, the API returns HTTP 429:

```json
{
  "detail": "Rate limit exceeded. Max 10 calls per 3600s."
}
```

## Error responses

| Status | Meaning |
|--------|---------|
| 400 | Invalid phone number or missing required field |
| 401 | Invalid or missing API key |
| 404 | Call not found |
| 409 | Agent not yet initialized or no pending approval |
| 429 | Rate limit exceeded |
| 504 | Takeover/resume acknowledgment timed out |

## Complete workflow example

```bash
# 1. Start a call
RESPONSE=$(curl -s -X POST http://localhost:8000/calls \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+18001234567", "instructions": "Cancel subscription", "approval_required": true}')

CALL_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "Call started: $CALL_ID"

# 2. Poll for status
sleep 10
curl -s http://localhost:8000/calls/$CALL_ID \
  -H "X-API-Key: your-key" | jq '.state'

# 3. Approve when the agent requests it
curl -s -X POST http://localhost:8000/calls/$CALL_ID/approve \
  -H "X-API-Key: your-key"

# 4. Or take over the call
curl -s -X POST http://localhost:8000/calls/$CALL_ID/takeover \
  -H "X-API-Key: your-key"

# 5. Resume agent control
curl -s -X POST http://localhost:8000/calls/$CALL_ID/resume \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"summary": "Confirmed the cancellation."}'
```

!!! warning "In-memory state"
    The REST API stores call-to-room mappings in memory. This state is lost on server restart. For production deployments, consider using LiveKit room metadata for call state recovery, or implement a persistent backend (Redis, database).

## Next steps

- [Python SDK guide](sdk.md) -- direct programmatic control
- [MCP Server guide](mcp-server.md) -- AI agent integration
- [Human takeover](human-takeover.md) -- detailed takeover flow
- [Approval flow](approval-flow.md) -- approval integration
