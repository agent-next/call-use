# call-use v0.1.0 — Press Kit

---

## One-Sentence Description

call-use is an open-source Python runtime that gives AI agents the ability to make real phone calls, navigate IVR menus, and have voice conversations — in 3 lines of code.

## One-Paragraph Description

call-use is an open-source outbound call-control runtime for AI agents. It bridges the gap between AI automation and the telephone network: developers can give any AI agent the ability to make real phone calls using 3 lines of Python. The agent dials a number, navigates automated phone menus (IVR), has real-time voice conversations, and reports back with a full transcript. Built on LiveKit for real-time audio, Twilio for telephony, GPT-4o for conversational intelligence, and Deepgram for speech-to-text, call-use ships with four interfaces — a Python SDK, CLI, MCP Server (for Claude Code integration), and REST API. Key safety features include human takeover (jump into any live call) and an approval flow (the agent pauses for confirmation before irreversible actions). MIT licensed and self-hostable.

## Key Facts

| | |
|---|---|
| **Product** | call-use |
| **Version** | v0.1.0 |
| **Category** | AI Agent Infrastructure / Voice AI / Developer Tools |
| **Tagline** | "The browser-use for phones" |
| **License** | MIT (fully open-source) |
| **Language** | Python |
| **GitHub** | https://github.com/agent-next/call-use |
| **Website** | https://call-use.com |
| **Docs** | https://docs.call-use.com |
| **Install** | `pip install call-use` |
| **Organization** | agent-next |

## Founder / Team Quote

> "AI agents can browse the web, write code, send emails, and interact with APIs — but they still can't pick up the phone. And thousands of everyday tasks still require a phone call. call-use bridges that gap. It's the missing voice layer for AI agents."
>
> — [Founder Name], creator of call-use

## Key Capabilities

- **Outbound PSTN calls** via Twilio SIP trunking
- **Real-time voice conversation** powered by GPT-4o + Deepgram STT
- **Automatic IVR navigation** (press 1, press 2, etc.)
- **Human takeover** — listen in and take control of any live call
- **Approval flow** — agent pauses for human confirmation before actions
- **Full call transcripts** returned after every call
- **4 interfaces**: Python SDK, CLI, MCP Server, REST API
- **Framework-agnostic** — works with LangChain, CrewAI, AutoGen, or standalone

## Use Cases

- Canceling subscriptions (cable, internet, insurance)
- Checking appointment availability (doctor, dentist, government)
- Navigating government phone systems (DMV, IRS, unemployment)
- Verifying insurance coverage or claims status
- Making reservations (restaurants, services)
- Gathering business information not available online

## Technical Stack

| Component | Technology | Role |
|-----------|-----------|------|
| Real-time audio | LiveKit | Bidirectional audio rooms, echo cancellation |
| Telephony | Twilio SIP | PSTN connectivity, phone number management |
| Conversation AI | GPT-4o | Reasoning, dialogue, task completion |
| Speech-to-text | Deepgram | Streaming STT with ~200ms latency |

## Cost Per Call (Approximate)

| Service | Cost/Minute |
|---------|-------------|
| Twilio | ~$0.014 |
| LiveKit (cloud) | ~$0.004 |
| GPT-4o | ~$0.01-0.03 |
| Deepgram | ~$0.0043 |
| **Total** | **~$0.03-0.05** |

LiveKit can be self-hosted for zero per-minute cost.

## Current Limitations (v0.1.0)

- Outbound calls only (inbound support planned for v0.2)
- US and Canada phone numbers only (international planned for v0.2)
- Requires Twilio and LiveKit accounts
- Best performance with standard IVR systems

## Roadmap

- **v0.2**: Inbound call handling, international numbers, local LLM support
- **v0.3**: Call scheduling, batch calls, webhook integrations
- **Future**: Multi-party calls, multi-language support

## Screenshots / Visuals

The following assets are available for press use:

1. **Code example** — 3-line Python snippet with syntax highlighting
2. **Architecture diagram** — Full system architecture showing LiveKit + Twilio + GPT-4o + Deepgram pipeline
3. **CLI screenshot** — Terminal showing a call being made via CLI
4. **MCP integration** — Claude Code making a phone call via call-use
5. **Demo video** — Real phone call being made and navigated by an AI agent

[Contact for high-resolution assets]

## Logo Usage

- The call-use logo and wordmark are available for editorial use
- Do not modify, rotate, or recolor the logo
- Maintain clear space around the logo
- [Link to brand assets / logo files]

## Press Contact

- **Email**: [press@call-use.com or founder email]
- **Twitter/X**: [@handle]
- **GitHub**: https://github.com/agent-next/call-use

## Boilerplate

**About call-use**: call-use is an open-source outbound call-control runtime that gives AI agents the ability to make real phone calls. Built on LiveKit, Twilio, GPT-4o, and Deepgram, it provides a simple Python SDK for developers to add voice calling capabilities to any AI agent. MIT licensed.

**About agent-next**: agent-next is an open-source organization building infrastructure for the next generation of AI agents. call-use is its first project.
