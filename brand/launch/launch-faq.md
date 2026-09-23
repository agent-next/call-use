# call-use v0.1.0 — Launch FAQ

Anticipated questions and prepared answers for launch day. Use these in HN comments, Reddit replies, Twitter responses, and GitHub discussions.

---

## "How is this different from Twilio's API?"

Twilio provides the telephony layer — it connects calls to the phone network. call-use builds on top of Twilio (and LiveKit, GPT-4o, Deepgram) to create a complete agent-controlled call experience.

Using raw Twilio, you'd need to:
- Build a real-time voice pipeline (bidirectional audio streaming)
- Integrate speech-to-text and text-to-speech
- Write the conversational AI logic
- Handle IVR detection and DTMF tone generation
- Build a call-control state machine
- Implement human takeover and approval flows

call-use handles all of this. Twilio is one component in the stack, not a competing product. Think of it this way: Twilio is the telephone wire. call-use is the agent that picks up the phone and talks.

---

## "Why not just use browser-use to navigate a web-based phone app?"

Three reasons:

1. **Latency.** Browser-based voice (WebRTC through a browser) adds significant overhead compared to direct SIP trunking. Phone conversations require sub-second response times. Routing audio through a browser UI, screen-reading it, and typing responses introduces multi-second delays that make conversation impossible.

2. **Reliability.** Browser automation is brittle — web UIs change, elements move, CAPTCHAs appear. Direct telephony via SIP is a standardized protocol that doesn't break when someone updates their CSS.

3. **Many tasks don't have a web option.** Try canceling certain insurance policies, reaching a specific government department, or checking availability at a small local business. Often the only interface is a phone number.

call-use and browser-use are complementary. browser-use handles the web. call-use handles the phone. Together, they cover most of how humans interact with businesses.

---

## "What about privacy / recording laws?"

This is an important topic and we take it seriously.

**Recording laws vary by jurisdiction:**
- Some US states require one-party consent (only one person on the call needs to know it's recorded)
- Other states require all-party consent (everyone must agree)
- Different countries have different rules

**Our recommendations:**
- Know the recording laws in your jurisdiction and the callee's jurisdiction
- The agent can be instructed to disclose that the call is being recorded or that it's an AI
- Use the approval flow feature to get human confirmation before sensitive calls
- call-use stores transcripts locally — you control your data

**What call-use does:**
- All data stays on your infrastructure (self-hosted)
- No call data is sent to call-use servers (there are none)
- Transcripts are stored locally, not in any cloud database
- You can configure the agent to identify itself as AI-assisted

**What call-use does NOT do:**
- We don't provide legal advice on recording laws
- We don't handle compliance for you
- We don't store, access, or transmit your call data

Users are responsible for ensuring their use of call-use complies with applicable laws.

---

## "Can this be used for spam calls / robocalls?"

We designed call-use for legitimate automation of tedious phone-based tasks — canceling subscriptions, checking availability, navigating government phone trees. Not for spam.

**Technical constraints that limit misuse:**
- Requires Twilio account (which has its own anti-abuse policies and KYC requirements)
- Twilio enforces STIR/SHAKEN caller ID authentication
- Each call requires LLM API calls (~$0.03-0.05/min), making mass spam economically impractical
- No batch calling or auto-dialer functionality in v0.1

**Policy:**
- Our license and terms prohibit use for unsolicited calls, fraud, or harassment
- Twilio's Acceptable Use Policy separately prohibits spam and robocalling
- Violating Twilio's AUP gets your account terminated

**Honest acknowledgment:** Any telephony tool can theoretically be misused, just as any email client can send spam. We've made design choices that make misuse impractical and have clear policies against it, but we can't prevent all possible misuse of open-source software.

---

## "What's the cost to run this?"

Approximate cost per minute of call time:

| Service | Cost/Min | Notes |
|---------|----------|-------|
| Twilio (telephony) | ~$0.014 | Pay-as-you-go, outbound US calls |
| LiveKit (cloud) | ~$0.004 | Free if self-hosted |
| GPT-4o (LLM) | ~$0.01-0.03 | Depends on conversation verbosity |
| Deepgram (STT) | ~$0.0043 | Pay-as-you-go |
| **Total** | **~$0.03-0.05** | |

**For a typical 5-minute call**: $0.15 - $0.25

**Monthly costs for moderate use (50 calls/month, avg 5 min each):**
- ~$7.50 - $12.50 in API costs
- Plus any base subscription fees for Twilio/LiveKit accounts

**Self-hosting LiveKit** reduces the LiveKit cost to zero (just your server costs).

**No call-use fees.** The project is open-source — there is no call-use subscription, per-call fee, or platform charge. You only pay the underlying service providers.

---

## "Does it work with non-US numbers?"

**v0.1.0**: US and Canada numbers only. This is a limitation of our current Twilio SIP configuration, not a fundamental architectural constraint.

**v0.2 (planned)**: International number support. Twilio supports calling 180+ countries, so the telephony layer is ready — we need to handle international dialing conventions, different IVR patterns, and multi-language support in the agent.

**If you need international calling now**: It's technically possible by modifying the Twilio SIP trunk configuration for international dialing, but it's not tested or officially supported in v0.1.

---

## "How reliable is it?"

**Honest assessment for v0.1.0:**

- **Call connection**: Very reliable. Twilio's SIP trunking is production-grade and connects calls consistently.
- **IVR navigation**: Works well for standard IVR systems (the "press 1 for billing" type). Can struggle with non-standard or poorly designed IVR menus, music-heavy hold systems, or unusual voice prompts.
- **Conversation quality**: Good for structured tasks (canceling a service, checking availability). Less reliable for open-ended or complex negotiations.
- **Human takeover**: Reliable — this is a straightforward audio routing switch.
- **Overall success rate**: We don't have enough production data to give a percentage. In our testing, straightforward tasks (IVR navigation + simple request) succeed most of the time. Complex multi-step conversations with pushback from the representative are less consistent.

**What affects reliability:**
- Quality of the task description (specific instructions help)
- Complexity of the IVR system
- How cooperative the human representative is
- Network conditions (affects audio quality)
- LLM performance (GPT-4o is generally good but not perfect)

**Our approach**: Ship v0.1 with honest limitations, gather production feedback, and improve reliability iteratively. We'd rather be transparent about limitations than oversell.

---

## "What's the latency?"

**End-to-end response latency** (time from human finishes speaking to agent starts speaking):

| Component | Latency |
|-----------|---------|
| Speech-to-text (Deepgram streaming) | ~200ms |
| LLM reasoning (GPT-4o) | ~300-500ms |
| Text-to-speech (streaming) | ~100-200ms |
| Network / SIP overhead | ~100ms |
| **Total (first response)** | **~700-1000ms** |
| **Total (subsequent turns)** | **~400-600ms** |

**Is this fast enough?** For phone conversations, yes. Humans expect some processing time in phone calls, especially business calls. A 0.5-1 second pause before responding is within the range of normal human conversation. It's noticeably faster than a human who needs to look something up before responding.

**Where latency matters most:** The first response after the other party finishes speaking. Subsequent responses can be faster because the conversation context is already loaded.

**What we're doing to reduce latency:**
- Streaming STT (partial transcripts before utterance is complete)
- Streaming TTS (start speaking before full response is generated)
- Speculative response generation (predict likely responses during human speech)
- These optimizations are partially implemented in v0.1, with more coming in v0.2

---

## "Can I use this with Claude / Anthropic instead of GPT-4o?"

Not in v0.1.0, but it's on the roadmap.

The architecture is designed to be model-agnostic — the LLM is a pluggable component. Currently GPT-4o is the default because it has strong real-time conversational ability and tool use support.

Adding Claude support requires:
- Adapting the prompt format for Claude's conversation style
- Handling tool use differences (function calling vs. tool use blocks)
- Testing conversational quality and latency

We plan to add Claude, Llama, and Mistral support in v0.2. If you want to contribute this, the LLM interface is well-defined — see the contributing guide.

---

## "How does IVR detection work?"

IVR (Interactive Voice Response) is the automated phone menu system — "Press 1 for billing, press 2 for technical support."

call-use detects and navigates IVR menus using:

1. **Content classification**: The STT transcript is analyzed by GPT-4o to determine if the speech is an IVR menu prompt or human conversation. IVR prompts have distinct patterns ("for X, press N").

2. **Audio analysis**: TTS-generated voices (used in most IVR systems) have different acoustic characteristics than human speech. We use this signal to help distinguish automated menus from humans.

3. **DTMF generation**: Once an IVR option is identified, call-use generates the appropriate DTMF tone (the "beep" when you press a number). Both in-band (audio) and out-of-band (SIP INFO) methods are supported for maximum compatibility.

4. **State tracking**: The call-control state machine tracks whether the call is in IVR navigation mode or conversation mode, adjusting the agent's behavior accordingly.

**Limitations**: Non-standard IVR systems (speech-recognition based menus like "say billing"), multi-language menus, and very long hold music sequences can be challenging.

---

## "Is this legal?"

We're not lawyers and this isn't legal advice.

Generally, making outbound phone calls is legal. Businesses and individuals make outbound calls every day. The legal considerations are:

1. **Recording laws**: Vary by jurisdiction (see the privacy question above). The agent can be configured to disclose recording.

2. **Robocall regulations**: The TCPA (in the US) and similar laws regulate automated calls. call-use is designed for agent-initiated, task-specific calls — not mass auto-dialing. Each call is individually initiated with a specific purpose.

3. **Fraud / impersonation**: Using AI to impersonate a specific person or to commit fraud is illegal regardless of the tool used. call-use's terms prohibit this.

4. **Business-specific policies**: Some businesses may have terms of service that affect automated calling. For example, a bank might prohibit automated calls to their customer service line.

**Our recommendation**: Use call-use for legitimate task automation with human oversight. Use the approval flow feature. Consult a lawyer if you're building a commercial product on top of call-use and have questions about compliance.

---

## "What happens if the call goes wrong?"

Several safety mechanisms:

1. **Human takeover**: You can jump into any live call at any moment. If the agent goes off-track, take control and finish the conversation yourself.

2. **Approval flow**: Configure the agent to pause and ask for your confirmation before taking important actions (confirming a cancellation, agreeing to terms, providing information).

3. **Timeout handling**: Calls have configurable maximum duration. If the call exceeds the limit, it ends gracefully.

4. **Task boundaries**: The agent is instructed to stay within the scope of its task description. It won't volunteer information or agree to things outside its mandate.

5. **Full transcript**: Every call produces a complete transcript so you can review exactly what was said.

**Worst case scenario**: The agent says something incorrect or off-task. The human on the other end will likely ask for clarification or escalate to a supervisor — the same thing that would happen if a human caller made an error. You can review the transcript afterward and follow up if needed.

---

## "Can I use my own phone number as the caller ID?"

Yes, with Twilio. Twilio allows you to configure verified phone numbers as your outbound caller ID. You'll need to verify ownership of the number through Twilio's standard verification process.

You can also purchase phone numbers through Twilio to use as dedicated caller IDs for your agent.

---

## "How do I contribute?"

We welcome contributions. Here's how to get started:

1. **Star the repo**: https://github.com/agent-next/call-use
2. **Check the issues**: Look for labels `good first issue` and `help wanted`
3. **Read the contributing guide**: CONTRIBUTING.md in the repo
4. **Join the community**: [Discord/GitHub Discussions link]

**Areas where we especially need help:**
- Additional LLM provider support (Claude, Llama, Mistral)
- International calling support
- IVR detection improvements
- Documentation and examples
- Testing with different phone systems
