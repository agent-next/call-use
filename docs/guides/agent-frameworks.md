# Agent Framework Integration

call-use works with any agent framework. Since the CLI outputs structured JSON to stdout, any agent that can run shell commands can make phone calls. For tighter integration, use the Python SDK directly.

## LangChain

Wrap the call-use CLI as a LangChain tool:

```python
import json
import subprocess
from langchain_core.tools import tool


@tool
def phone_call(phone: str, instructions: str, user_info: str = "{}") -> str:
    """Make a phone call via AI agent. Returns JSON with transcript and outcome.

    Args:
        phone: Target phone number in E.164 format (e.g., +18001234567)
        instructions: What to accomplish on the call
        user_info: JSON string with context (e.g., '{"name": "Alice"}')
    """
    result = subprocess.run(
        ["call-use", "dial", phone, "-i", instructions, "-u", user_info],
        capture_output=True,
        text=True,
        timeout=660,
    )
    if result.returncode == 2:
        return json.dumps({"error": f"Input error: {result.stderr.strip()}"})
    if result.returncode != 0 and not result.stdout.strip():
        return json.dumps(
            {"error": f"Call failed (exit {result.returncode}): {result.stderr.strip()}"}
        )
    return result.stdout
```

Use with any LangChain agent:

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-4o")
agent = create_react_agent(llm, [phone_call])
agent.invoke({"input": "Call +18001234567 and ask about store hours"})
```

## OpenAI Agents SDK

Wrap call-use as an OpenAI Agents tool:

```python
import json
import subprocess
from agents import Agent, Runner, function_tool


@function_tool
def phone_call(phone: str, instructions: str, user_info: str = "{}") -> str:
    """Make a phone call via AI agent. Returns JSON with transcript and outcome.

    Args:
        phone: Target phone number in E.164 format (e.g., +18001234567)
        instructions: What to accomplish on the call
        user_info: JSON string with context (e.g., '{"name": "Alice"}')
    """
    result = subprocess.run(
        ["call-use", "dial", phone, "-i", instructions, "-u", user_info],
        capture_output=True,
        text=True,
        timeout=660,
    )
    if result.returncode == 2:
        return json.dumps({"error": f"Input error: {result.stderr.strip()}"})
    if result.returncode != 0 and not result.stdout.strip():
        return json.dumps(
            {"error": f"Call failed (exit {result.returncode}): {result.stderr.strip()}"}
        )
    return result.stdout


agent = Agent(
    name="Phone Agent",
    instructions="You help users by making phone calls on their behalf.",
    tools=[phone_call],
)

# Run:
# Runner.run_sync(agent, "Call Comcast at +18001234567 and cancel my subscription")
```

## CrewAI

Wrap call-use as a CrewAI tool:

```python
import json
import subprocess
from crewai.tools import tool


@tool("phone_call")
def phone_call(phone: str, instructions: str, user_info: str = "{}") -> str:
    """Make a phone call via AI agent. Returns JSON with transcript and outcome.
    phone: Target phone number in E.164 format (e.g., +18001234567).
    instructions: What to accomplish on the call.
    user_info: JSON string with context (e.g., '{"name": "Alice"}').
    """
    result = subprocess.run(
        ["call-use", "dial", phone, "-i", instructions, "-u", user_info],
        capture_output=True,
        text=True,
        timeout=660,
    )
    if result.returncode == 2:
        return json.dumps({"error": f"Input error: {result.stderr.strip()}"})
    if result.returncode != 0 and not result.stdout.strip():
        return json.dumps(
            {"error": f"Call failed (exit {result.returncode}): {result.stderr.strip()}"}
        )
    return result.stdout
```

## Claude Code (via MCP)

Claude Code integrates natively via the MCP server -- no wrapper needed:

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

See the [MCP Server guide](mcp-server.md) for full setup instructions.

## Any agent that runs bash

If your agent can execute shell commands, it can use call-use:

```bash
call-use dial "+18001234567" -i "Ask about store hours"
```

The JSON result goes to stdout, making it easy to parse in any language:

```bash
# Get just the disposition
call-use dial "+18001234567" -i "Ask about hours" | jq -r '.disposition'

# Get the full transcript
call-use dial "+18001234567" -i "Ask about hours" | jq '.transcript'
```

## Direct SDK integration

For maximum flexibility, use the Python SDK directly in your agent code:

```python
import asyncio
from call_use import CallAgent


async def make_call(phone: str, instructions: str, user_info: dict = None) -> dict:
    """Make a call and return the outcome as a dict."""
    agent = CallAgent(
        phone=phone,
        instructions=instructions,
        user_info=user_info or {},
        approval_required=False,
    )
    outcome = await agent.call()
    return outcome.model_dump(mode="json")
```

This gives you access to event streaming, human takeover, and approval flow -- features not available through the CLI wrapper approach.

## Choosing an integration method

| Method | Best for | Approval flow | Events | Human takeover |
|--------|----------|:---:|:---:|:---:|
| CLI wrapper | Quick integration, any framework | Interactive only | stderr | No |
| MCP server | Claude Code, Codex | No | No | No |
| Python SDK | Full control, production use | Yes | Yes | Yes |
| REST API | Multi-tenant, server-side | Yes | Via LiveKit | Yes |

## Next steps

- [SDK guide](sdk.md) -- full Python SDK reference
- [CLI guide](cli.md) -- CLI flags and options
- [MCP Server guide](mcp-server.md) -- MCP setup details
- [REST API guide](rest-api.md) -- deploy as a service
