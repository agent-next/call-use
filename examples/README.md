# call-use Examples

Real-world examples showing how to use **call-use** — the open-source AI phone agent runtime.

## Quick Start

```bash
pip install call-use
export LIVEKIT_URL=wss://your-project.livekit.cloud
export LIVEKIT_API_KEY=your-key
export LIVEKIT_API_SECRET=your-secret
export SIP_TRUNK_ID=your-trunk-id
export OPENAI_API_KEY=sk-...
```

---

## Examples

| File | Description | Difficulty |
|------|-------------|------------|
| [cs_refund_agent.py](cs_refund_agent.py) | Customer service refund — baseline example | Beginner |
| [appointment_scheduler.py](appointment_scheduler.py) | Book a doctor appointment via IVR | Beginner |
| [subscription_cancellation.py](subscription_cancellation.py) | Cancel a subscription; handle retention offers | Beginner |
| [insurance_claim.py](insurance_claim.py) | File an auto insurance claim; capture claim number | Intermediate |
| [multi_call_workflow.py](multi_call_workflow.py) | Chain two calls: check balance → request credit increase | Intermediate |
| [webhook_integration.py](webhook_integration.py) | FastAPI server with WebSocket event streaming | Advanced |
| [langchain_tool.py](langchain_tool.py) | Use call-use as a LangChain tool | Intermediate |
| [openai_agents.py](openai_agents.py) | Use call-use inside OpenAI Agents SDK | Intermediate |
| [crewai_integration.py](crewai_integration.py) | Use call-use inside a CrewAI crew | Intermediate |
| [claude_code_setup.md](claude_code_setup.md) | Configure Claude Code to make calls via MCP | Beginner |

---

## Patterns Demonstrated

### Approval Flow
Request human sign-off before the agent commits to an action (booking, cancellation, etc.):
```python
def on_approval(details):
    print(f"APPROVAL NEEDED: {details.get('details')}")
    return "approved" if input("Approve? (y/n): ").strip() == "y" else "rejected"

agent = CallAgent(..., on_approval=on_approval)
```

### Event Streaming
React to transcripts, state changes, and actions in real time:
```python
def on_event(event):
    if event.type.value == "transcript":
        print(f"[{event.data['speaker']}] {event.data['text']}")
    elif event.type.value == "state_change":
        print(f"State: {event.data['from']} -> {event.data['to']}")
```

### Multi-Call Chaining
Run multiple `CallAgent` calls sequentially and pass data between them:
```python
outcome1 = await agent1.call()
# inspect outcome1.transcript, outcome1.summary ...
outcome2 = await agent2.call()
```

### Framework Integration
Use `subprocess` to wrap the `call-use` CLI as a tool in any agent framework:
```python
result = subprocess.run(
    ["call-use", "dial", phone, "-i", instructions],
    capture_output=True, text=True, timeout=660,
)
```

---

## Running an Example

```bash
# Appointment scheduler
python examples/appointment_scheduler.py "+18005551234" "Schedule a checkup for next week"

# Subscription cancellation (gym)
python examples/subscription_cancellation.py "+18005551234" "gym"

# Insurance claim (uses default fake number)
python examples/insurance_claim.py "+18005551234"

# Multi-call workflow
python examples/multi_call_workflow.py

# Webhook server (requires fastapi + uvicorn)
pip install fastapi uvicorn
uvicorn examples.webhook_integration:app --reload
```
