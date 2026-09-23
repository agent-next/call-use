# call-use v0.1.0 — Email Templates

All templates are ready to customize and send. Replace bracketed placeholders before sending.

---

## 1. Cold Pitch to Newsletter Editors

**Subject**: Open-source tool that gives AI agents the ability to make phone calls

**Body**:

```
Hi [Name],

I'm [your name], and I just open-sourced call-use — a Python runtime that
gives AI agents the ability to make real phone calls.

The pitch: AI agents can browse the web, write code, send emails, and call
APIs. But they can't pick up the phone. call-use fixes that with 3 lines
of Python.

    from call_use import CallAgent
    agent = CallAgent(task="Cancel my Comcast subscription", phone="+18001234567")
    result = await agent.call()

The agent dials the number, navigates the IVR menu, has a voice conversation,
and reports back with a transcript.

Key details:
- Open-source, MIT licensed
- Built on LiveKit + Twilio + GPT-4o + Deepgram
- 4 interfaces: Python SDK, CLI, MCP Server, REST API
- Safety: human takeover + approval flow built in
- GitHub: https://github.com/agent-next/call-use

I think this would resonate with [newsletter name]'s audience because
[specific reason — e.g., "your readers are building AI agents and this
adds a new capability to their toolkit"].

Happy to provide any additional details, a demo, or answer questions.

Best,
[Your name]
[Your Twitter/X handle]
```

---

## 2. Cold Pitch to Podcast Hosts

**Subject**: Guest pitch — building the "browser-use for phone calls"

**Body**:

```
Hi [Name],

I'm a fan of [podcast name] — [mention a specific recent episode that's
relevant, e.g., "the episode with X about AI agents was great"].

I just released call-use, an open-source runtime that lets AI agents make
real phone calls. It's been described as "the browser-use for phones."

I think this could make for an interesting conversation because:

1. It's a new capability for AI agents that didn't exist before — agents
   can now navigate IVR menus, have voice conversations, and complete
   phone-based tasks autonomously.

2. The engineering is non-trivial — bridging real-time voice, telephony
   (SIP/PSTN), LLMs, and speech-to-text into a reliable pipeline has
   interesting technical challenges around latency, turn-taking, and
   IVR detection.

3. The safety and ethics angle — autonomous phone calls raise important
   questions about consent, recording laws, and preventing misuse. We've
   built in human oversight (takeover + approval flow), but the broader
   implications are worth discussing.

Background on me: [2-3 sentences about your background and credibility]

The project launched [date] and has [X stars / Y installs / notable
traction]. GitHub: https://github.com/agent-next/call-use

Would you be open to a conversation? I'm flexible on timing and format.

Best,
[Your name]
[Your Twitter/X handle]
[Your website]
```

---

## 3. Cold Pitch to AI Influencers (Twitter DM or Email)

**Subject**: Built something I think you'd find interesting — AI agents that make phone calls

**Body** (shorter, more casual):

```
Hey [Name],

Big fan of your work on [specific thing they've done recently].

I just shipped call-use — an open-source runtime that lets AI agents
make real phone calls. 3 lines of Python, and your agent can dial a
number, navigate IVR menus, and have a conversation.

Think "browser-use for phones."

Quick demo: [link to video]
GitHub: https://github.com/agent-next/call-use

No pressure at all, but if this is interesting to you I'd love your
feedback. And if you wanted to share it with your audience, I'd
obviously appreciate that too.

[Your name]
```

---

## 4. Follow-Up Email (Send 5-7 Days After Initial Pitch)

**Subject**: Re: [original subject line]

**Body**:

```
Hi [Name],

Following up on my email from last week about call-use — the open-source
tool that lets AI agents make phone calls.

Since launch, the project has [gotten X GitHub stars / been featured on
HN with Y points / had Z installs / other traction metric]. [Optional:
mention any notable coverage or community response.]

Here's a 2-minute demo if that's easier than reading: [video link]

If the timing isn't right or it's not a fit for [newsletter/podcast/audience],
no worries at all. Just wanted to make sure it didn't get lost in the inbox.

Best,
[Your name]
```

---

## 5. Pitch to Tech Blog / Media Reporter

**Subject**: Open-source project lets AI agents make real phone calls — just launched

**Body**:

```
Hi [Name],

I'm reaching out because you cover [AI/developer tools/voice AI] for
[publication], and I think this might be relevant.

I just released call-use, an open-source Python runtime that gives AI
agents the ability to make real outbound phone calls. The agent dials a
real phone number, navigates automated phone menus, has a voice
conversation with a human, and reports back.

Why it matters:
- AI agents can automate nearly everything digital, but phone calls
  remain a manual task
- Thousands of business processes still require a phone call (canceling
  services, scheduling appointments, navigating government systems)
- call-use is the first open-source tool that bridges AI agents and the
  telephone network

Key details:
- 3 lines of Python to make a call
- Built on LiveKit + Twilio + GPT-4o + Deepgram
- MIT licensed, self-hostable, no vendor lock-in
- Safety: human takeover and approval flow built in
- GitHub: https://github.com/agent-next/call-use
- Launched [date], [traction stats]

I'm available for an interview, demo, or any questions. I can also
provide technical details on the architecture and engineering challenges.

Best,
[Your name]
[Title / affiliation]
[Contact info]
```

---

## Tips for All Outreach

1. **Personalize every email.** Reference something specific about the recipient's recent work. Generic pitches get deleted.

2. **Lead with what it does, not what it is.** "AI agents can now make phone calls" beats "I built an open-source outbound call-control runtime."

3. **Include traction.** After launch day, always include current GitHub stars, installs, HN points, or other social proof.

4. **Keep it short.** Newsletter editors and podcast hosts get dozens of pitches. Respect their time. The pitch should be scannable in 30 seconds.

5. **One ask per email.** Don't ask for a newsletter feature AND a podcast interview AND a tweet in the same email.

6. **Follow up once.** If no response after 5-7 days, send one follow-up. After that, move on.

7. **Timing matters.** Send pitches Tuesday-Thursday, 9-11 AM in the recipient's timezone. Avoid Monday mornings and Friday afternoons.

8. **Demo beats description.** A 60-second video of a real call is more compelling than 500 words of explanation. Always include a demo link.
