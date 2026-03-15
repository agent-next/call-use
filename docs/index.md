---
hide:
  - navigation
  - toc
---

# call-use

**Give your AI agent the ability to make phone calls.** The [browser-use](https://github.com/browser-use/browser-use) for phones.

---

## Three lines to make a phone call

```python
from call_use import CallAgent

outcome = await CallAgent(phone="+18001234567", instructions="Cancel my subscription").call()
print(outcome.disposition)  # "completed"
```

---

## What it does

call-use is an open-source outbound call-control runtime that lets AI agents make real phone calls. It handles dialing, IVR navigation, conversation, and structured reporting -- so your agent can focus on the task.

- **Dials outbound** via Twilio SIP trunk through LiveKit
- **Talks** using Deepgram STT, GPT-4o LLM, and GPT-4o-mini TTS
- **Reports** structured `CallOutcome` with full transcript, events, and disposition
- **Human takeover** -- pause the AI mid-call and take over the conversation
- **Approval flow** -- agent asks for human sign-off before sensitive actions
- **4 interfaces** -- Python SDK, REST API, CLI, and MCP Server

---

## Why call-use?

| | call-use | Build from scratch | Pine AI |
|---|:---:|:---:|:---:|
| Make a phone call | 3 lines | months | sign up + $$$ |
| IVR navigation | built-in | weeks | built-in |
| Live transcript | built-in | weeks | built-in |
| Human takeover | built-in | weeks | -- |
| Approval flow | built-in | days | -- |
| Open source | yes | -- | no |
| Self-hostable | yes | -- | no |
| Any agent framework | yes | -- | no |

---

## Works with

Claude Code -- LangChain -- OpenAI Agents -- CrewAI -- Any agent that runs bash

---

## Install

```bash
pip install call-use
```

---

## Choose your interface

=== "Python SDK"

    ```python
    import asyncio
    from call_use import CallAgent

    async def main():
        agent = CallAgent(
            phone="+18001234567",
            instructions="Ask about store hours",
            approval_required=False,
        )
        outcome = await agent.call()
        print(f"Done: {outcome.disposition.value}")

    asyncio.run(main())
    ```

=== "CLI"

    ```bash
    call-use dial "+18001234567" -i "Ask about store hours"
    ```

=== "MCP Server"

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

=== "REST API"

    ```bash
    curl -X POST http://localhost:8000/calls \
      -H "X-API-Key: your-key" \
      -H "Content-Type: application/json" \
      -d '{"phone_number": "+18001234567", "instructions": "Ask about store hours"}'
    ```

---

## Next steps

<div class="grid cards" markdown>

-   **Getting Started**

    ---

    Install call-use, configure your environment, and make your first call.

    [:octicons-arrow-right-24: Getting started](getting-started/index.md)

-   **Guides**

    ---

    Deep dives into each interface: SDK, CLI, REST API, MCP, and more.

    [:octicons-arrow-right-24: Guides](guides/sdk.md)

-   **API Reference**

    ---

    Auto-generated reference for all classes, functions, and data models.

    [:octicons-arrow-right-24: Reference](reference/api.md)

-   **Architecture**

    ---

    How call-use works under the hood: data flow, state machine, components.

    [:octicons-arrow-right-24: Architecture](architecture/index.md)

</div>
