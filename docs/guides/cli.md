# CLI

The `call-use` CLI lets any agent that can run bash make phone calls. Events stream to stderr in real time, and the structured JSON result goes to stdout -- making it easy to pipe into other tools.

## Quick start

```bash
call-use dial "+18001234567" -i "Ask about store hours"
```

## Commands

### `call-use dial`

Make an outbound phone call.

```
call-use dial PHONE [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `PHONE` | Target phone number in E.164 format (e.g., `+18001234567`) |

**Options:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--instructions` | `-i` | `str` | (required) | What the agent should do on the call |
| `--user-info` | `-u` | `str` | `None` | JSON dict of context for the agent |
| `--caller-id` | | `str` | `None` | Outbound caller ID (E.164) |
| `--voice-id` | | `str` | `None` | TTS voice: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` |
| `--timeout` | | `int` | `600` | Max call duration in seconds |
| `--approval-required` | | flag | `False` | Require interactive approval for sensitive actions |

### `call-use doctor`

Check that all required environment variables are set and that LiveKit is reachable. This is the fastest way to verify your setup before making a call.

```bash
call-use doctor
```

The command checks six environment variables (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `SIP_TRUNK_ID`, `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`) and then attempts to connect to your LiveKit server.

**Example output (all configured):**

```
  ✓ LIVEKIT_URL set
  ✓ LIVEKIT_API_KEY set
  ✓ LIVEKIT_API_SECRET set
  ✓ SIP_TRUNK_ID set
  ✓ OPENAI_API_KEY set
  ✓ DEEPGRAM_API_KEY set
  ✓ LiveKit connection OK

  7 passed, 0 failed
```

**Example output (partial configuration):**

```
  ✓ LIVEKIT_URL set
  ✓ LIVEKIT_API_KEY set
  ✓ LIVEKIT_API_SECRET set
  ✗ SIP_TRUNK_ID missing
  ✗ OPENAI_API_KEY missing
  ✓ DEEPGRAM_API_KEY set
  ✗ LiveKit connection failed: ...

  3 passed, 4 failed
```

**When to use it:**

- After first-time setup, to confirm every credential is in place.
- When a call fails unexpectedly, to rule out configuration issues.
- In CI, as a smoke test before running integration tests.

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | One or more checks failed |

### `call-use --version`

Print the installed version.

```bash
call-use --version
```

## Examples

### Basic call

```bash
call-use dial "+18001234567" -i "Ask about store hours"
```

### With user context

Pass user information as a JSON string:

```bash
call-use dial "+18005551234" \
  -i "Cancel my subscription" \
  -u '{"account_number": "12345", "name": "Alice Smith"}'
```

### Custom voice and caller ID

```bash
call-use dial "+18005551234" \
  -i "Schedule an appointment for next Tuesday" \
  --voice-id nova \
  --caller-id "+15551234567"
```

### With approval flow

When `--approval-required` is set, the CLI prompts on stdin for approval:

```bash
call-use dial "+18005551234" \
  -i "Negotiate a lower rate on my internet bill" \
  --approval-required
```

Output:

```
Calling +18005551234...
  state: connected
  [agent] Hi, I'm calling about my internet bill...
  [callee] The best I can offer is $49.99 per month.
  APPROVAL NEEDED: Accept $49.99/month rate
  Approve? [y/n]: y
  [agent] That sounds great, I'll accept that.
  state: ended
```

### With timeout

Set a shorter timeout for quick calls:

```bash
call-use dial "+18001234567" -i "Ask about hours" --timeout 120
```

## Output format

### stderr (real-time events)

Events stream to stderr as they happen:

```
Calling +18001234567...
  state: dialing
  state: connected
  [agent] Hi, I'm calling to ask about your business hours.
  [callee] We're open 9 to 5, Monday through Friday.
  [agent] Thank you, have a great day!
  state: ended
```

Event types printed:

- **Transcript**: `[speaker] text`
- **State changes**: `state: new_state`
- **Approval requests**: `APPROVAL NEEDED: details`

### stdout (structured JSON)

The final result is printed to stdout as JSON:

```json
{
  "task_id": "task-a1b2c3d4",
  "transcript": [
    {"speaker": "agent", "text": "Hi, I'm calling to ask about your business hours.", "timestamp": 1710000000.0},
    {"speaker": "callee", "text": "We're open 9 to 5, Monday through Friday.", "timestamp": 1710000005.0}
  ],
  "events": [...],
  "duration_seconds": 45.2,
  "disposition": "completed",
  "recording_url": null,
  "metadata": {}
}
```

## Piping and automation

Since events go to stderr and JSON goes to stdout, you can pipe the result:

### Extract disposition with jq

```bash
call-use dial "+18001234567" -i "Ask about hours" | jq '.disposition'
```

### Save transcript to file

```bash
call-use dial "+18001234567" -i "Ask about hours" | jq '.transcript' > transcript.json
```

### Use in a shell script

```bash
#!/bin/bash
result=$(call-use dial "+18001234567" -i "Ask about store hours" 2>/dev/null)
disposition=$(echo "$result" | jq -r '.disposition')

if [ "$disposition" = "completed" ]; then
    echo "Call succeeded!"
    echo "$result" | jq '.transcript'
else
    echo "Call failed: $disposition"
    exit 1
fi
```

### Chain with other CLI tools

```bash
# Call and send result to an API
call-use dial "+18001234567" -i "Get account balance" \
  | curl -X POST https://your-api.com/results \
    -H "Content-Type: application/json" \
    -d @-
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Call completed with an expected disposition (`completed`, `voicemail`, `no_answer`, `busy`) |
| `1` | Call failed, timed out, or encountered an error |
| `2` | Invalid input (bad phone number, invalid JSON for `--user-info`) |

## Environment variables

The CLI loads `.env` automatically via `python-dotenv`. Required variables:

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `SIP_TRUNK_ID` | Twilio SIP trunk ID |
| `OPENAI_API_KEY` | OpenAI API key |

If any are missing, the CLI prints a clear error and exits with code 1.

## Next steps

- [Python SDK guide](sdk.md) -- programmatic control with async/await
- [MCP Server guide](mcp-server.md) -- integrate with Claude Code and other AI agents
- [REST API guide](rest-api.md) -- deploy as a service
