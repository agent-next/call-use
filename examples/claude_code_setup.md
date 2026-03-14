# Using call-use with Claude Code

## Setup

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "call-use": {
      "command": "call-use-mcp",
      "env": {
        "LIVEKIT_URL": "wss://your-project.livekit.cloud",
        "LIVEKIT_API_KEY": "your-key",
        "LIVEKIT_API_SECRET": "your-secret",
        "SIP_TRUNK_ID": "your-trunk-id",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

## Usage

Once configured, Claude Code can make phone calls:

> "Call +18001234567 and ask about their store hours"

Claude will use the `dial` tool automatically, then poll `status` and retrieve the `result`.
