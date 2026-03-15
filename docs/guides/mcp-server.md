# MCP Server

The call-use MCP server exposes phone calling as tools for AI agents that support the [Model Context Protocol](https://modelcontextprotocol.io/). This lets Claude Code, Codex, and other MCP-compatible agents make phone calls natively.

## How it works

The MCP server provides 4 async tools:

| Tool | Description |
|------|-------------|
| `dial` | Dispatch an outbound call (non-blocking, returns `task_id`) |
| `status` | Check the current state of a call |
| `cancel` | Cancel an active call |
| `result` | Retrieve the final outcome after a call completes |

The workflow is: `dial` -> poll `status` -> when finished, call `result`.

Calls are non-blocking. The `dial` tool dispatches the call and returns immediately with a `task_id`. The agent then polls `status` until the call ends, and retrieves the full outcome with `result`.

## Setup for Claude Code

Add to your Claude Code MCP configuration (`~/.claude/mcp.json` or project-level `.claude/mcp.json`):

```json
{
  "mcpServers": {
    "call-use": {
      "command": "call-use-mcp",
      "env": {
        "LIVEKIT_URL": "wss://your-project.livekit.cloud",
        "LIVEKIT_API_KEY": "APIxxxxxxxx",
        "LIVEKIT_API_SECRET": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "SIP_TRUNK_ID": "ST_xxxxxxxxxxxxxxxxxxxxxxxx",
        "OPENAI_API_KEY": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

After configuring, Claude Code will have access to the `dial`, `status`, `cancel`, and `result` tools.

## Setup for Codex

Add to your Codex MCP configuration:

```json
{
  "mcpServers": {
    "call-use": {
      "command": "call-use-mcp",
      "env": {
        "LIVEKIT_URL": "wss://...",
        "LIVEKIT_API_KEY": "...",
        "LIVEKIT_API_SECRET": "...",
        "SIP_TRUNK_ID": "...",
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

## Tool reference

### dial

Dispatch an outbound phone call. Returns immediately with a `task_id`.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `phone` | `str` | Yes | -- | Target number in E.164 format (US/Canada only) |
| `instructions` | `str` | Yes | -- | What the agent should accomplish |
| `user_info` | `str` | No | `None` | JSON string with context for the agent |
| `caller_id` | `str` | No | `None` | Outbound caller ID (E.164) |
| `voice_id` | `str` | No | `"alloy"` | TTS voice: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` |
| `timeout` | `int` | No | `600` | Max call duration in seconds |

**Returns:**

```json
{
  "task_id": "call-a1b2c3d4e5f6",
  "status": "dispatched"
}
```

!!! note "Approval not supported in MCP"
    The MCP server sets `approval_required=False` for all calls. The non-blocking async design is not compatible with the synchronous approval callback pattern. Use the Python SDK or REST API if you need approval flow.

### status

Check the current state of a phone call.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | `str` | Yes | The `task_id` returned by `dial` |

**Returns:**

```json
{
  "task_id": "call-a1b2c3d4e5f6",
  "state": "connected"
}
```

Possible states: `unknown`, `dialing`, `ringing`, `connected`, `in_ivr`, `on_hold`, `in_conversation`, `awaiting_approval`, `human_takeover`, `ended`.

### cancel

Cancel an active phone call.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | `str` | Yes | The `task_id` of the call to cancel |

**Returns:**

```json
{
  "task_id": "call-a1b2c3d4e5f6",
  "status": "cancel_requested"
}
```

### result

Retrieve the final outcome after a call completes.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | `str` | Yes | The `task_id` returned by `dial` |

**Returns (when complete):**

```json
{
  "task_id": "call-a1b2c3d4e5f6",
  "transcript": [
    {"speaker": "agent", "text": "Hi, I'm calling about store hours.", "timestamp": 1710000000.0},
    {"speaker": "callee", "text": "We're open 9 to 5.", "timestamp": 1710000005.0}
  ],
  "events": [...],
  "duration_seconds": 32.5,
  "disposition": "completed",
  "recording_url": null,
  "metadata": {"phone_number": "+18001234567", "caller_id": null}
}
```

**Returns (still in progress):**

```json
{
  "task_id": "call-a1b2c3d4e5f6",
  "status": "in_progress",
  "state": "connected"
}
```

## Example agent interaction

Here is what a typical Claude Code interaction looks like with call-use MCP tools:

```
User: Call Comcast at +18001234567 and ask about my current plan details.
       My account number is 98765.

Claude: I'll call Comcast for you. Let me dispatch the call.

[uses dial tool: phone="+18001234567",
 instructions="Ask about current plan details",
 user_info='{"account_number": "98765"}']

The call has been dispatched with task_id call-a1b2c3d4e5f6.
Let me check the status.

[uses status tool: task_id="call-a1b2c3d4e5f6"]

The call is currently connected. I'll check again in a moment.

[uses status tool: task_id="call-a1b2c3d4e5f6"]

The call has ended. Let me get the results.

[uses result tool: task_id="call-a1b2c3d4e5f6"]

The call is complete. Here's what I found:
- Your current plan is the Performance Pro at $79.99/month
- It includes 400 Mbps download speed
- Your contract renews on April 15th
```

## Running the MCP server manually

The MCP server uses stdio transport by default:

```bash
call-use-mcp
```

This is typically not run manually -- it is launched by the MCP client (Claude Code, Codex, etc.) based on your configuration.

## Environment variables

The MCP server requires the same environment variables as all other interfaces:

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL (`wss://...`) |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `SIP_TRUNK_ID` | Twilio SIP trunk ID |
| `OPENAI_API_KEY` | OpenAI API key |

These are passed via the `env` field in your MCP configuration.

## Next steps

- [CLI guide](cli.md) -- use call-use from the terminal
- [Python SDK guide](sdk.md) -- programmatic control with approval flow
- [REST API guide](rest-api.md) -- deploy as a multi-tenant service
