---
date: 2026-03-14
authors:
  - agent-next
categories:
  - Release
  - Announcement
description: "Introducing call-use: the open-source runtime that gives AI agents the ability to make phone calls."
---

# Introducing call-use: the browser-use for phones

AI agents can browse the web, write code, query databases, and draft emails. But when the task requires picking up the phone -- calling an insurance company, scheduling an appointment, or canceling a subscription -- they hit a wall. The phone network is the one channel that AI agents still cannot reach.

Today we are releasing **call-use v0.1.0**, an open-source outbound call-control runtime that gives any AI agent the ability to make real phone calls.

<!-- more -->

## What is call-use?

call-use is a self-hostable Python runtime that connects AI agents to the public telephone network. It handles the entire call lifecycle: dialing via Twilio SIP, managing the voice pipeline (Deepgram STT, GPT-4o LLM, OpenAI TTS), navigating IVR menus, and returning a structured outcome with a full transcript.

Think of it as the [browser-use](https://github.com/browser-use/browser-use) for phones. Where browser-use gives agents a browser, call-use gives them a phone.

It is framework-agnostic. It works with LangChain, OpenAI Agents SDK, Claude Code (via MCP), CrewAI, or any agent that can run a shell command.

## Three lines to make a call

```python
from call_use import CallAgent

outcome = await CallAgent(phone="+18001234567", instructions="Cancel my subscription").call()
print(outcome.disposition)  # "completed"
```

That is the minimal example. For a real-world use case, here is a customer service refund agent with live transcript streaming and an approval gate:

```python
import asyncio
from call_use import CallAgent

async def main():
    def on_event(event):
        if event.type.value == "transcript":
            speaker = event.data.get("speaker", "?")
            print(f"  [{speaker}] {event.data.get('text', '')}")

    def on_approval(details):
        print(f"  APPROVAL NEEDED: {details.get('details', '')}")
        return "approved" if input("  Approve? (y/n): ").strip().lower() == "y" else "rejected"

    agent = CallAgent(
        phone="+18001234567",
        instructions="Get a refund for order #12345. The customer's name is Alice.",
        user_info={"name": "Alice", "order_id": "12345"},
        on_event=on_event,
        on_approval=on_approval,
    )

    outcome = await agent.call()
    print(f"Disposition: {outcome.disposition.value}")
    print(f"Duration: {outcome.duration_seconds:.1f}s")
    print(f"Transcript: {len(outcome.transcript)} turns")

asyncio.run(main())
```

The agent dials the number, navigates the IVR, waits on hold, speaks to a representative, and returns a structured `CallOutcome` with the full transcript and disposition.

## Why we built this

A surprising number of business processes still require a phone call. Filing an insurance claim. Scheduling a doctor's appointment. Canceling a cable subscription. Disputing a charge. Calling a utility provider about a bill.

AI agent frameworks have matured rapidly over the past year, but they all share the same blind spot: they cannot interact with the phone network. When an agent's task requires making a call, it either gives up or asks the human to do it.

We built call-use to close that gap. It is MIT-licensed, self-hostable, and designed to be a building block -- not a platform you sign up for.

## Key features

### IVR navigation

Most business phone lines start with an automated menu. call-use handles this natively: it listens to the IVR prompts, generates DTMF tones to navigate menus, detects voicemail greetings, and recognizes when it has reached a human representative.

### Human takeover

Sometimes the agent needs help, or you want to take over mid-call. The human takeover flow pauses the AI agent and gives you a LiveKit token to join the call directly. When you are done, hand control back to the agent.

```python
token = await agent.takeover()   # Pause agent, get join token
# ... join the LiveKit room, talk to the other party ...
await agent.resume()             # Hand back to agent
```

### Approval flow

For sensitive actions -- confirming a payment, agreeing to terms, authorizing a cancellation -- the agent can pause and ask for human approval before proceeding. The `on_approval` callback lets you build this into any workflow.

### Structured outcomes

Every call produces a `CallOutcome` with:

- **disposition**: `completed`, `failed`, `voicemail`, `no_answer`, `busy`, `timeout`, or `cancelled`
- **transcript**: full conversation as a list of `{speaker, text, timestamp}` entries
- **events**: timestamped call events (state changes, DTMF tones, approvals)
- **duration**: total call length in seconds

No parsing required. The outcome is a Pydantic model that your agent can reason over directly.

### Four interfaces

| Interface | Best for |
|-----------|----------|
| **Python SDK** | Direct integration in async Python code |
| **CLI** | Any agent that can run bash (`call-use dial "+1..." -i "..."`) |
| **MCP Server** | Claude Code, Codex, and other MCP-compatible agents |
| **REST API** | Multi-tenant deployments, server-to-server integrations |

Pick whichever fits your stack. They all produce the same `CallOutcome`.

## Architecture

call-use runs as two processes:

```
+----------------+         +----------------+         +----------------+
|  Your code     |-------->|  LiveKit       |-------->|  Twilio SIP    |
|  (CallAgent)   |  room   |  Cloud/OSS     |  trunk  |  -> PSTN       |
+----------------+         +----------------+         +----------------+
                                 |
                           +-----+------+
                           | call-use   |
                           | worker     |
                           | (Agent)    |
                           +------------+
```

1. **Your code** (or the REST API / CLI / MCP server) creates a LiveKit room and dispatches an agent via the LiveKit Agents framework.
2. **The call-use worker** joins the room, dials the target number through the SIP trunk, runs the voice pipeline (STT + LLM + TTS), handles the conversation, and publishes the outcome back through the LiveKit data channel.

The two processes communicate entirely through LiveKit -- data channels for events and commands, room metadata for state. This means the SDK process and the worker can run on different machines, and you get room-level isolation for free.

## Works with everything

call-use is designed to be a tool, not a framework. It exposes a CLI and an MCP server, so any agent that can run a subprocess or call an MCP tool can make phone calls.

**LangChain:**

```python
from langchain_core.tools import tool

@tool
def phone_call(phone: str, instructions: str) -> str:
    """Make a phone call via AI agent."""
    result = subprocess.run(
        ["call-use", "dial", phone, "-i", instructions],
        capture_output=True, text=True, timeout=660,
    )
    return result.stdout
```

**OpenAI Agents SDK:**

```python
from agents import Agent, function_tool

@function_tool
def phone_call(phone: str, instructions: str) -> str:
    """Make a phone call via AI agent."""
    result = subprocess.run(
        ["call-use", "dial", phone, "-i", instructions],
        capture_output=True, text=True, timeout=660,
    )
    return result.stdout

agent = Agent(name="Phone Agent", tools=[phone_call])
```

**Claude Code (MCP):**

```json
{
  "mcpServers": {
    "call-use": {
      "command": "call-use-mcp",
      "env": {
        "LIVEKIT_URL": "wss://your-project.livekit.cloud",
        "LIVEKIT_API_KEY": "...",
        "LIVEKIT_API_SECRET": "...",
        "SIP_TRUNK_ID": "...",
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

**Any bash-capable agent:**

```bash
call-use dial "+18001234567" -i "Ask about store hours"
# stdout: {"task_id": "...", "disposition": "completed", "transcript": [...]}
```

## Getting started

**1. Install**

```bash
pip install call-use
```

**2. Configure**

You need accounts with LiveKit, Twilio (SIP trunk), Deepgram, and OpenAI. Set these environment variables:

```bash
export LIVEKIT_URL="wss://your-project.livekit.cloud"
export LIVEKIT_API_KEY="your-key"
export LIVEKIT_API_SECRET="your-secret"
export SIP_TRUNK_ID="your-twilio-sip-trunk-id"
export DEEPGRAM_API_KEY="your-deepgram-key"
export OPENAI_API_KEY="your-openai-key"
```

**3. Start the worker**

```bash
call-use-worker start
```

**4. Make a call**

```python
from call_use import CallAgent

outcome = await CallAgent(
    phone="+18001234567",
    instructions="Ask about store hours",
    approval_required=False,
).call()
```

Or from the command line:

```bash
call-use dial "+18001234567" -i "Ask about store hours"
```

## What's next

v0.1.0 is the foundation. Here is what we are working on for v0.2:

- **Caller ID verification** -- validate number ownership via Twilio Lookup API, not just format
- **Inbound call support** -- receive and handle incoming calls, not just outbound
- **Persistence backend** -- pluggable state storage (Redis, PostgreSQL) so call state survives restarts
- **WebRTC support** -- browser-to-browser calls without going through the PSTN
- **Horizontal scaling** -- shared state backend for running multiple worker instances

## Try it

call-use is MIT-licensed and available now.

- **GitHub**: [github.com/agent-next/call-use](https://github.com/agent-next/call-use)
- **PyPI**: `pip install call-use`
- **Docs**: See the [README](https://github.com/agent-next/call-use#readme) for full API reference

Star the repo if this is useful. Open an issue if something breaks. Pull requests are welcome -- check [CONTRIBUTING.md](https://github.com/agent-next/call-use/blob/main/CONTRIBUTING.md) for guidelines.

If your AI agent needs to make a phone call, now it can.
