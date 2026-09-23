# call-use v0.1.0 — Social Media Content

All content is ready to post. Adjust handles, links, and images before publishing.

---

## Twitter/X Launch Thread

### Tweet 1 — Hook
```
AI agents can browse the web, write code, send emails, and book flights.

But they still can't pick up the phone.

Until now.

Introducing call-use — open-source outbound call-control for AI agents.

github.com/agent-next/call-use
```

### Tweet 2 — Code Example
```
3 lines of Python to make a real phone call:

from call_use import CallAgent
agent = CallAgent(task="Cancel my Comcast subscription", phone="+18001234567")
result = await agent.call()

That's it. Your agent dials the number, navigates the IVR, talks to a human, and reports back.

[Attach: code screenshot with syntax highlighting]
```

### Tweet 3 — Key Features
```
What call-use handles:

- Outbound PSTN calls via Twilio SIP
- Real-time voice conversation (GPT-4o + Deepgram STT)
- IVR navigation ("press 1 for billing...")
- Human takeover — jump into any live call
- Approval flow — agent asks before acting
- Full call transcripts
```

### Tweet 4 — Architecture
```
Under the hood:

LiveKit — real-time audio rooms
Twilio — SIP trunking to PSTN
GPT-4o — conversational intelligence
Deepgram — speech-to-text (~200ms latency)

Everything connects through a call-control state machine that handles the full lifecycle of a phone call.

[Attach: architecture diagram]
```

### Tweet 5 — Demo
```
Here's call-use canceling a subscription in real time.

The agent:
1. Dials the number
2. Navigates the IVR menu
3. Waits on hold
4. Talks to the representative
5. Confirms the cancellation
6. Reports back with a transcript

[Attach: demo video or GIF]
```

### Tweet 6 — Framework Compatibility
```
call-use works as a tool in any agent framework:

- LangChain / LangGraph
- CrewAI
- AutoGen
- Custom agents

Or use it standalone — SDK, CLI, REST API, or MCP Server.

It's a capability layer, not a framework.
```

### Tweet 7 — Human Takeover
```
The killer feature: human takeover.

At any point during a call, you can:
- Listen in on the live audio
- Take over the conversation
- Give the agent new instructions

Your agent starts the call. You finish it if needed. Best of both worlds.
```

### Tweet 8 — MCP Integration
```
call-use ships with an MCP server.

That means you can use it directly from Claude Code:

"Call Comcast and cancel my internet subscription"

Claude Code connects to call-use, makes the call, and reports back.

AI agents + phone calls + natural language. No code required.
```

### Tweet 9 — Open Source
```
call-use is:

- Open-source (MIT license)
- Self-hostable
- No vendor lock-in
- No per-call platform fees (just Twilio + LLM costs)

Your calls, your infrastructure, your data.

github.com/agent-next/call-use
```

### Tweet 10 — Getting Started
```
Get started in 60 seconds:

pip install call-use
call-use init  # set up API keys
call-use call --task "Check if Dr. Smith has availability on Friday" --phone "+15551234567"

Full docs: docs.call-use.com
PyPI: pypi.org/project/call-use
```

### Tweet 11 — Roadmap
```
What's coming in v0.2:

- Inbound call handling
- International number support
- Local LLM support (Llama, Mistral)
- Call scheduling and batching
- Webhook integrations
- Multi-party calls

What would you want to see? Reply or open an issue.
```

### Tweet 12 — CTA
```
If you've ever wished your AI agent could just call someone — call-use is for you.

Star it: github.com/agent-next/call-use
Try it: pip install call-use
Read the docs: docs.call-use.com
Contribute: issues labeled "good first issue"

Built by @[handle] and the agent-next community.
```

---

## LinkedIn Launch Post

```
I just open-sourced call-use — a runtime that gives AI agents the ability to make real phone calls.

The problem: AI agents can browse the web, send emails, write code, and interact with APIs. But thousands of business processes still require a phone call. Canceling services. Checking appointment availability. Navigating government agencies. Verifying insurance claims. These tasks still require a human picking up a phone and waiting on hold.

call-use fixes this. 3 lines of Python:

    from call_use import CallAgent
    agent = CallAgent(task="Cancel my subscription", phone="+18001234567")
    result = await agent.call()

Your agent dials the number, navigates the IVR menu, has a real-time voice conversation, and reports back with a full transcript.

Key capabilities:
- Outbound PSTN calls via Twilio SIP trunking
- Real-time voice powered by GPT-4o + Deepgram STT
- Automatic IVR navigation
- Human takeover — jump into any live call at any time
- Approval flow — agent asks before taking irreversible actions
- 4 interfaces: Python SDK, CLI, MCP Server, REST API

The tech stack: LiveKit for real-time audio, Twilio for telephony, GPT-4o for conversation, Deepgram for speech-to-text. All orchestrated by a call-control state machine.

This is v0.1.0 — outbound calls, US/Canada numbers, and a solid foundation. International support, inbound calls, and local LLM integration are on the roadmap.

MIT licensed. Self-hostable. No platform lock-in.

I'm looking for feedback from engineering teams who deal with phone-based workflows, and contributors who want to help build the voice layer for AI agents.

GitHub: https://github.com/agent-next/call-use
Docs: https://docs.call-use.com
Website: https://call-use.com

#opensource #AIagents #voiceAI #Python #automation
```

---

## LinkedIn Technical Deep-Dive Post (T+1)

```
Yesterday I open-sourced call-use. Today I want to share the engineering decisions behind it.

The core challenge: bridging an AI agent's text-based reasoning with a real-time voice phone call. These are fundamentally different communication modalities with different latency requirements.

Here's how the architecture works:

1. Telephony Layer (Twilio)
Twilio SIP trunking connects to the PSTN. When call-use initiates a call, it creates a SIP INVITE through Twilio, which bridges to a real phone number. Cost: ~$0.014/min.

2. Real-Time Audio (LiveKit)
LiveKit manages the audio room. The Twilio SIP trunk connects to a LiveKit room, where the AI participant also lives. This gives us low-latency bidirectional audio with built-in echo cancellation and noise suppression.

3. Speech-to-Text (Deepgram)
We chose Deepgram over Whisper for a simple reason: latency. Deepgram's streaming STT delivers partial transcripts in ~200ms. Whisper, even with optimizations, typically requires 1-2 second chunks. In a phone conversation, that delay is the difference between natural and awkward.

4. Conversational AI (GPT-4o)
GPT-4o handles the actual conversation — understanding what the human said, deciding what to say next, and taking actions (like pressing DTMF tones for IVR menus). We feed it the task description, conversation history, and available actions.

5. Call-Control State Machine
The glue that holds everything together. States: dialing, ringing, connected, ivr_navigating, speaking, listening, on_hold, human_takeover, completed. Each state has defined transitions and timeout handlers.

The hardest problem was IVR detection. How do you know when a robot voice says "press 1 for billing" versus a human saying "one"? We use a combination of audio analysis (TTS voices have distinct patterns) and content classification (GPT-4o identifies menu prompts vs. conversational speech).

Latency budget:
- STT: ~200ms (Deepgram streaming)
- LLM reasoning: ~300-500ms (GPT-4o)
- TTS: ~100-200ms (streaming)
- Network/SIP: ~100ms
- Total: ~700-1000ms first response, ~400-600ms subsequent

For phone conversations, this is acceptable. Humans expect some processing delay, especially in professional/business calls.

What I'd do differently: invest more in the IVR detection early on. It's the most brittle part of the system and the most impactful for reliability.

Full source: https://github.com/agent-next/call-use

If you're building voice AI or have experience with telephony systems, I'd especially value your input.
```

---

## Reddit Posts

### r/Python

**Title**: `call-use: 3 lines of Python to give your AI agent the ability to make phone calls (open-source, MIT)`

**Body**:
```
I just open-sourced call-use — an outbound call-control runtime that lets
AI agents make real phone calls.

    from call_use import CallAgent
    agent = CallAgent(
        task="Cancel my Comcast subscription",
        phone="+18001234567"
    )
    result = await agent.call()

It handles IVR navigation (press 1 for billing...), real-time voice
conversation, and lets you take over any live call.

4 interfaces:
- **Python SDK** (async-first, fully typed)
- **CLI** (`call-use call --task "..." --phone "..."`)
- **MCP Server** (works with Claude Code)
- **REST API**

Built with LiveKit (real-time audio), Twilio (telephony), GPT-4o
(conversation), and Deepgram (STT).

MIT licensed. `pip install call-use`

- GitHub: https://github.com/agent-next/call-use
- Docs: https://docs.call-use.com
- PyPI: https://pypi.org/project/call-use

This is v0.1.0 — outbound calls, US/Canada numbers. International and
inbound support are planned for v0.2.

Looking for feedback on the API design. The SDK is async-first with
full type annotations. Happy to hear what you'd change.
```

### r/MachineLearning

**Title**: `[P] call-use: Open-source runtime for AI agents to make outbound phone calls (LiveKit + GPT-4o + Deepgram)`

**Body**:
```
I'm releasing call-use, an open-source outbound call-control runtime that
bridges AI agents with the PSTN (public telephone network).

**The problem**: AI agents can interact with web APIs, browsers, and text
interfaces, but phone calls remain a gap. Many real-world tasks — appointment
scheduling, service cancellation, insurance verification — require voice
interaction over phone.

**Architecture**:
- Twilio SIP trunking for PSTN connectivity
- LiveKit for real-time bidirectional audio
- Deepgram streaming STT (~200ms partial transcript latency)
- GPT-4o for conversational reasoning and IVR navigation
- Call-control state machine managing the full call lifecycle

**Key technical challenges**:
1. IVR detection: distinguishing automated menu prompts from human speech
   using audio pattern analysis + content classification
2. Latency budget: ~700-1000ms end-to-end for first response (STT 200ms +
   LLM 300-500ms + TTS 100-200ms + network 100ms)
3. DTMF tone generation: sending in-band and out-of-band tones for IVR
   menu navigation
4. Turn-taking: detecting when the human has finished speaking to avoid
   interruptions

**What it's not**: This is not a voice cloning project or a social
engineering tool. It's designed for legitimate automation of tedious
phone-based tasks with human oversight (approval flow, live takeover).

MIT licensed. Python SDK, CLI, MCP Server, REST API.

- GitHub: https://github.com/agent-next/call-use
- Paper/technical writeup: [coming soon]

Interested in feedback on the IVR detection approach and ideas for
reducing end-to-end latency.
```

### r/LangChain

**Title**: `call-use: Add phone call capabilities to your LangChain agents (open-source, MIT)`

**Body**:
```
I built call-use — an open-source runtime that lets AI agents make real
phone calls. It works as a tool in LangChain/LangGraph agents.

**Use case**: Your agent is researching something and needs to call a
business to check hours, verify availability, or get information that
isn't online. Now it can.

**Integration**: call-use exposes a simple async Python API that can be
wrapped as a LangChain tool:

    from call_use import CallAgent

    async def make_phone_call(task: str, phone: str) -> str:
        agent = CallAgent(task=task, phone=phone)
        result = await agent.call()
        return result.transcript

Add this as a tool in your agent's toolkit and it gains the ability to
make phone calls as part of its reasoning chain.

Also ships with an **MCP Server** for Claude Code integration, a **CLI**
for quick testing, and a **REST API** for service-to-service usage.

Built on LiveKit + Twilio + GPT-4o + Deepgram.

GitHub: https://github.com/agent-next/call-use
Docs: https://docs.call-use.com

Would love to hear what phone-based tasks you'd automate with your
LangChain agents.
```

### r/artificial

**Title**: `Open-source project that gives AI agents the ability to make real phone calls — navigate IVR menus, talk to humans, cancel subscriptions`

**Body**:
```
I just released call-use, an open-source tool that lets AI agents make
real outbound phone calls.

**What it does**: You give it a task ("cancel my Comcast subscription")
and a phone number. It dials the number, navigates the IVR menu (press
1 for billing...), talks to the human representative, and completes
the task. You get a full transcript and result.

**Key features**:
- Automatic IVR navigation
- Real-time voice conversation
- Human takeover (you can jump in at any point)
- Approval flow (agent asks before doing anything irreversible)

**Why it matters**: AI agents can do almost everything digitally —
browse the web, send emails, write code, interact with APIs. But
thousands of tasks still require a phone call. This bridges that gap.

**Safety**: Built with oversight in mind. The approval flow means the
agent will pause and ask for your confirmation before taking important
actions. You can listen in and take over any call at any time.

MIT licensed, open-source, self-hostable.

Demo: [link]
GitHub: https://github.com/agent-next/call-use

This is v0.1 — outbound calls to US/Canada numbers. International
support and inbound calls are on the roadmap.
```

### r/LocalLLaMA

**Title**: `call-use: Open-source phone call runtime for AI agents — currently GPT-4o, looking for input on local LLM support`

**Body**:
```
I just open-sourced call-use — a runtime that lets AI agents make real
outbound phone calls. Currently uses GPT-4o for the conversational
intelligence, but the architecture is designed to be model-agnostic.

**Why I'm posting here**: I want to add support for local LLMs and I'd
value this community's input on what would work best for real-time voice
conversation.

**Requirements for the LLM component**:
- Fast inference (~300-500ms for a response)
- Good at following complex instructions (task completion)
- Conversational ability (natural phone dialogue)
- Tool use (DTMF tones, call control actions)

**Candidates I'm considering**:
- Llama 3.1 70B (good quality but latency?)
- Mistral Large (tool use support)
- Smaller models with fine-tuning for phone conversation

The latency budget is tight — total end-to-end needs to be under 1
second for natural conversation. STT takes ~200ms (Deepgram) and TTS
takes ~150ms, leaving ~400-500ms for the LLM.

Has anyone here run local LLMs with streaming output at that latency?
What model + hardware combination would you recommend?

GitHub: https://github.com/agent-next/call-use
```

### r/ChatGPT

**Title**: `I built an open-source tool that lets AI agents make real phone calls — here's it canceling a subscription`

**Body**:
```
What if your AI could call Comcast and cancel your subscription for you?

I built call-use — an open-source tool that gives AI agents the ability
to make real phone calls. You give it a task and a phone number, and it
handles the rest.

[Demo video/GIF here]

**How it works**:
1. You describe the task: "Cancel my internet subscription"
2. You provide the phone number
3. The AI dials, navigates the phone menu, talks to the rep, and
   reports back

**Cool features**:
- It can navigate those annoying "press 1 for billing" menus automatically
- You can listen in and take over the call at any point
- It asks for your approval before doing anything important
- You get a full transcript of the entire call

It uses GPT-4o for the conversation part, so it sounds natural and
can handle complex discussions.

Free and open-source: https://github.com/agent-next/call-use

(You do need Twilio and OpenAI accounts for the telephony and AI parts,
which have their own per-minute costs — roughly $0.03-0.05/min total.)
```

### r/programming

**Title**: `call-use: Open-source outbound call-control runtime for AI agents (Python, LiveKit, Twilio SIP, MIT)`

**Body**:
```
I'm releasing call-use, an open-source outbound call-control runtime
that lets AI agents make real PSTN phone calls.

**Architecture**:

    [AI Agent] → [call-use SDK] → [LiveKit Room] ↔ [Twilio SIP Trunk] → [PSTN]
                                       ↕
                              [Deepgram STT / TTS]
                                       ↕
                                   [GPT-4o]

The interesting engineering challenges:

1. **SIP bridging**: Twilio's SIP trunking connects to a LiveKit room
   via SIP participant. The AI agent joins the same room as another
   participant. LiveKit handles mixing and routing.

2. **IVR detection**: Distinguishing recorded menu prompts from human
   speech. Uses a combination of audio pattern analysis and content
   classification.

3. **DTMF generation**: Both in-band (audio tones) and out-of-band
   (SIP INFO) for maximum IVR compatibility.

4. **Turn-taking**: Endpointing detection to know when the human has
   finished speaking. Uses VAD (voice activity detection) + silence
   duration + content analysis.

5. **Latency pipeline**: STT (~200ms, Deepgram streaming) → LLM
   (~300-500ms, GPT-4o) → TTS (~150ms, streaming) → audio out.
   Total ~700-1000ms, acceptable for phone conversation.

**Interfaces**: Python SDK (async), CLI, MCP Server, REST API.

MIT licensed. Not a SaaS — you run it on your infra.

GitHub: https://github.com/agent-next/call-use
Docs: https://docs.call-use.com
```
