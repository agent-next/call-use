# call-use v0.1.0 Launch Plan

## Overview

**Product**: call-use -- open-source outbound call-control runtime for AI agents
**Version**: v0.1.0
**Tagline**: "The browser-use for phones"
**GitHub**: https://github.com/agent-next/call-use
**Website**: https://call-use.com
**Docs**: https://docs.call-use.com

---

## Timeline

### T-7: Pre-Launch Prep

- [ ] All launch documents finalized and reviewed
- [ ] GitHub repo public, README polished, examples working
- [ ] Website live with docs, quickstart, and install instructions
- [ ] Social accounts claimed: Twitter/X (@calluse or @call_use), LinkedIn page
- [ ] Demo video recorded (2-3 min real call demonstration)
- [ ] Code screenshot images generated (3-line example, architecture diagram)
- [ ] Product Hunt listing drafted (do not publish)
- [ ] Blog post drafted on dev.to / hashnode (do not publish)
- [ ] Discord server or GitHub Discussions enabled for community
- [ ] Prepare a list of 10-15 early testers who can star + try it before launch

### T-3: Seed Content

- [ ] Send early access to 5-10 AI influencers with a personal note
- [ ] Share teaser on Twitter/X: "Something new for AI agents is coming..."
- [ ] Post in close developer communities (private Discords, Slack groups) for early feedback
- [ ] Ensure all influencers have install instructions and can reproduce the demo
- [ ] Confirm Product Hunt hunter (if using a hunter) or self-launch plan
- [ ] Draft HN Show HN post and first comment

### T-1: Final Checks

- [ ] Run through quickstart on a clean machine -- must work in under 5 minutes
- [ ] Verify all links: GitHub, docs, website, PyPI package
- [ ] Pre-schedule tweets (or have them ready in a thread composer)
- [ ] Confirm Product Hunt launch is queued for T-0
- [ ] Brief anyone who agreed to share/retweet on launch day
- [ ] Test demo video plays correctly, code screenshots are legible

### T-0: Launch Day (Hour by Hour)

All times in Pacific Time (PT). Adjust for your timezone.

| Time (PT) | Action |
|-----------|--------|
| 00:01 | Product Hunt listing goes live (auto-publish at midnight) |
| 06:00 | Post Show HN on Hacker News |
| 06:05 | Post first comment on HN with technical details |
| 06:15 | Publish Twitter/X launch thread |
| 06:30 | Post on r/Python (technical angle) |
| 06:45 | Post on r/MachineLearning (research/capability angle) |
| 07:00 | Post on r/LangChain (integration angle) |
| 07:15 | Publish LinkedIn announcement post |
| 07:30 | Post in AI Discord communities (Latent Space, MLOps, etc.) |
| 08:00 | Publish dev.to / Hashnode tutorial article |
| 08:30 | Send pitch emails to newsletter editors |
| 09:00 | Monitor HN, respond to every comment within 30 minutes |
| 10:00 | Post on r/artificial, r/LocalLLaMA, r/ChatGPT |
| 12:00 | Midday check: respond to all GitHub issues, tweets, comments |
| 14:00 | Post follow-up tweet with early stats ("100 stars in 6 hours") |
| 16:00 | Post on r/programming |
| 18:00 | Evening check: respond to all new comments/issues |
| 20:00 | Thank-you tweet to everyone who shared |

### T+1: Day After

- [ ] Respond to every GitHub issue and discussion
- [ ] Follow up on HN comments (the thread often peaks at 12-24 hours)
- [ ] Post "Day 1 stats" tweet (stars, installs, calls made)
- [ ] Upvote and engage with Product Hunt comments
- [ ] Send follow-up DMs to influencers who haven't shared yet
- [ ] Publish LinkedIn technical deep-dive post

### T+2 to T+3

- [ ] Publish "How I built call-use" narrative article
- [ ] Send cold pitches to podcast hosts
- [ ] Engage with any blog posts or videos others have created
- [ ] Post Twitter thread on architecture decisions
- [ ] Address top GitHub issues / feature requests publicly

### T+4 to T+7

- [ ] Compile launch retrospective: what worked, what didn't
- [ ] Publish a "Week 1 learnings" tweet thread
- [ ] Send pitch to AI newsletters for their next issue
- [ ] Plan v0.2 roadmap based on community feedback
- [ ] Start contributor onboarding for interested developers
- [ ] Create "good first issue" labels on GitHub for newcomers

---

## Platform-by-Platform Strategy

### Hacker News

**Format**: Show HN

**Title Options** (ranked by expected performance):

1. `Show HN: Call-Use -- Give your AI agent the ability to make phone calls`
2. `Show HN: Call-Use -- Open-source outbound call runtime for AI agents`
3. `Show HN: Call-Use -- The browser-use for phone calls (3 lines of Python)`
4. `Show HN: Call-Use -- AI agents can now navigate IVR menus and talk to humans`
5. `Show HN: Call-Use -- Open-source SDK to let AI agents make real phone calls`

**Recommended**: Option 1 -- clear, descriptive, matches the project's tagline.

**Best Posting Time**: Tuesday or Wednesday, 6:00-7:00 AM PT (9:00-10:00 AM ET). Avoids Monday noise and Friday dropoff. Early morning catches the East Coast workday start and European afternoon.

**Show HN Post**:

```
Show HN: Call-Use -- Give your AI agent the ability to make phone calls

call-use is an open-source outbound call-control runtime that lets AI agents
make real phone calls. Think of it as "browser-use for phones."

3 lines of Python:

    from call_use import CallAgent
    agent = CallAgent(task="Cancel my Comcast subscription", phone="+18001234567")
    result = await agent.call()

What it does:
- Makes outbound PSTN calls via Twilio SIP trunking
- Real-time voice conversation using GPT-4o + Deepgram STT
- Navigates IVR menus (press 1, press 2...) automatically
- Human takeover: you can jump into any live call
- Approval flow: agent asks permission before taking actions

4 interfaces: Python SDK, CLI, MCP Server (works with Claude Code), REST API.

Built on LiveKit for real-time audio, Twilio for telephony, GPT-4o for
conversation, Deepgram for speech-to-text.

MIT licensed. Self-hostable.

GitHub: https://github.com/agent-next/call-use
Docs: https://docs.call-use.com
Website: https://call-use.com
```

**First Comment Strategy**:

Post immediately after submitting. Include:
- Personal motivation ("I built this because...")
- Honest limitations (v0.1, US/Canada PSTN only, requires Twilio + LiveKit accounts)
- Technical decisions (why LiveKit over alternatives, why Deepgram over Whisper)
- What you're looking for (feedback, contributors, use cases)
- Cost breakdown (approximate per-call cost)

**Draft First Comment**:

```
Hey HN, I'm [name], the author.

I built call-use because I kept running into tasks where the only option was to
call a phone number -- canceling subscriptions, checking appointment availability,
navigating government phone trees. AI agents can browse the web, write code, and
send emails, but they couldn't pick up a phone. This fixes that.

Some honest limitations in v0.1.0:
- Outbound calls only (no inbound yet)
- US/Canada numbers only (international in v0.2)
- Requires Twilio and LiveKit accounts (not free, but pay-as-you-go)
- Latency is ~800ms for first response, ~400ms for subsequent turns
- IVR detection works well for standard menus but can struggle with
  non-standard systems

Cost breakdown per call:
- Twilio: ~$0.014/min
- LiveKit: ~$0.004/min (self-hosted: free)
- GPT-4o: ~$0.01-0.03/min depending on verbosity
- Deepgram: ~$0.0043/min
- Total: roughly $0.03-0.05/min

Technical choices:
- LiveKit over raw WebRTC: better reliability, built-in room management
- Deepgram over Whisper: lower latency for real-time STT (~200ms vs ~1s)
- GPT-4o over Claude: better at conversational flow (may add Claude support)

I'd love feedback on the API design, use cases you'd want to see, and
contributions. The MCP server integration means you can use this from
Claude Code today.
```

**Engagement Rules**:
- Respond to every comment, especially critical ones
- Be technical and honest -- HN rewards transparency about limitations
- Don't be defensive about "why not just use X" questions
- Upvote thoughtful comments, even critical ones

---

### Reddit

**Target Subreddits and Tailored Posts**:

#### r/Python
**Title**: `call-use: 3 lines of Python to give your AI agent the ability to make phone calls (open-source, MIT)`

**Post**: Focus on the Python developer experience. Lead with code, show the SDK API, mention async support, type hints, and clean API design.

#### r/MachineLearning
**Title**: `[P] call-use: Open-source runtime for AI agents to make outbound phone calls (LiveKit + GPT-4o + Deepgram)`

**Post**: Focus on the ML/AI architecture. Discuss the voice pipeline, STT/TTS choices, agent architecture, and where ML components fit.

#### r/LangChain
**Title**: `call-use: Add phone call capabilities to your LangChain/LangGraph agents (open-source)`

**Post**: Focus on integration with existing agent frameworks. Show how call-use can be a tool in a LangChain agent's toolkit.

#### r/artificial
**Title**: `Open-source project that gives AI agents the ability to make real phone calls -- navigate IVR menus, talk to humans, cancel subscriptions`

**Post**: Focus on the capability and use cases. Less code, more "here's what it can do" with concrete examples.

#### r/LocalLLaMA
**Title**: `call-use: Open-source call runtime for AI agents. Currently GPT-4o, but architecture supports swappable LLMs`

**Post**: Acknowledge it currently uses GPT-4o but explain the architecture allows plugging in local models. Ask for feedback on local LLM integration priorities.

#### r/ChatGPT
**Title**: `I built an open-source tool that lets AI agents make real phone calls -- here's a demo of it canceling a subscription`

**Post**: Focus on the demo and end-user impact. Include a video/GIF. Less technical, more "look what AI can do now."

#### r/programming
**Title**: `call-use: Open-source outbound call-control runtime for AI agents (Python, MIT license)`

**Post**: Focus on the engineering: architecture, protocol choices, how SIP trunking works, the real-time audio pipeline.

**Full post text for each subreddit**: See `social-content.md`.

**Timing**: Stagger posts across 4-6 hours to avoid looking like spam. Start with r/Python (highest relevance), then r/MachineLearning, then others.

**Rules**: Follow each subreddit's posting guidelines. Don't cross-post the same text. Engage with every comment.

---

### Twitter/X

**Launch Thread**: See `social-content.md` for full 12-tweet thread.

**Key Visuals**:
1. Code screenshot: 3-line Python example with syntax highlighting
2. Architecture diagram: LiveKit + Twilio + GPT-4o + Deepgram pipeline
3. Demo GIF or video: real call being made and navigated
4. Terminal screenshot: CLI usage
5. MCP integration screenshot: Claude Code making a call

**Hashtags**: #opensource #AIagents #voiceAI #Python #buildinpublic

**Accounts to Tag**:
- @laborai (browser-use)
- @LiveKit
- @DeepgramAI
- @OpenAI
- @AnthropicAI (Claude Code / MCP angle)
- @LangChainAI
- @CrewAIInc
- AI agent influencers: @svpino, @theaievangelist, @mattshumer_, @DrJimFan, @kaborofficial

**Follow-up Schedule**:
- T+1: Share a specific use case demo (e.g., booking a restaurant)
- T+2: Architecture deep-dive thread
- T+3: Share community feedback / early user stories
- T+4: MCP integration tutorial thread
- T+5: "What should we build for v0.2?" poll
- T+6: Contributor spotlight or "how to contribute" thread
- T+7: Week 1 retrospective with stats

---

### LinkedIn

**Post 1 (Launch Day)**: Professional announcement. See `social-content.md`.

**Post 2 (T+1)**: Technical deep-dive on the architecture and engineering decisions. Target: engineering leaders evaluating AI capabilities for their teams.

**Target Audience**: CTOs, VP Engineering, AI/ML leads, product managers working on AI automation.

**Engagement Strategy**: Tag relevant connections, respond to every comment, share in relevant LinkedIn groups.

---

### Product Hunt

**Best Launch Day**: Tuesday or Wednesday. Avoid Monday (high competition) and Friday (low traffic).

**Best Time**: Product Hunt resets at midnight PT. Listing should go live at 00:01 PT.

**Tagline**: "Give your AI agent the ability to make phone calls"

**Description**:
```
call-use is an open-source outbound call-control runtime for AI agents.
3 lines of Python to make a real phone call.

Your AI agent can now:
- Navigate IVR menus automatically (press 1 for billing...)
- Have real-time voice conversations
- Let you take over any live call
- Ask for your approval before taking actions

4 ways to use it:
- Python SDK
- CLI
- MCP Server (works with Claude Code)
- REST API

Built on LiveKit + Twilio + GPT-4o + Deepgram.
MIT licensed. Self-hostable. Open-source.
```

**First Comment (Maker Comment)**:
```
Hi Product Hunt! I'm [name], the maker of call-use.

I built this because AI agents can browse the web, write code, send emails --
but they can't pick up the phone. And so many tasks still require a phone
call: canceling subscriptions, checking appointment availability, navigating
government agencies.

call-use gives any AI agent the ability to make real outbound phone calls.
It handles the entire voice pipeline: Twilio for telephony, LiveKit for
real-time audio, GPT-4o for conversation, Deepgram for speech-to-text.

It's v0.1.0, so there are limitations (US/Canada only, outbound only), but
the foundation is solid and I'd love your feedback on what to build next.

Try it: pip install call-use
GitHub: https://github.com/agent-next/call-use
Docs: https://docs.call-use.com
```

**Visuals Needed**:
1. Hero image / logo (1270x760 px)
2. Gallery images (3-5): code example, architecture, demo screenshot, CLI, MCP
3. Demo video or GIF (optional but highly recommended)

---

### Dev.to / Hashnode

**Article 1: Technical Tutorial**
Title: "How to Give Your AI Agent the Ability to Make Phone Calls with call-use"

Outline:
1. Introduction -- the problem (AI agents can't use phones)
2. What is call-use?
3. Prerequisites (Twilio account, LiveKit, API keys)
4. Installation and setup
5. Making your first call (step-by-step with code)
6. Navigating an IVR menu
7. Human takeover feature
8. Using the MCP server with Claude Code
9. Architecture overview
10. What's next

**Article 2: Narrative / "How I Built" Article**
Title: "Building call-use: How I Gave AI Agents the Ability to Make Phone Calls"

Outline:
1. The moment of frustration (the task that sparked the idea)
2. Prior art -- what existed and why it wasn't enough
3. Architecture decisions (why LiveKit, why Deepgram, why not Whisper)
4. The hardest engineering problems (IVR detection, latency, SIP bridging)
5. The "it works" moment (first successful call)
6. Open-sourcing and what I learned
7. What's next for call-use

---

### Discord / Slack Communities

**Target Communities**:
- Latent Space Discord
- MLOps Community Slack
- AI Engineer Discord
- LangChain Discord
- LiveKit Discord / Community
- Deepgram Community
- Python Discord (#showcase channel)
- Anthropic Discord (if available)
- IndieHackers community

**Message Template** (adapt per community):
```
Just open-sourced call-use -- an outbound call-control runtime that lets
AI agents make real phone calls. 3 lines of Python.

Think "browser-use for phones." It handles IVR navigation, real-time voice
conversation, human takeover, and approval flows.

Built on LiveKit + Twilio + GPT-4o + Deepgram. MIT licensed.

GitHub: https://github.com/agent-next/call-use
Quick demo: [link to video]

Would love feedback from this community, especially on [specific topic
relevant to this community].
```

**Rules**: Don't spam. Post in the appropriate channel (#showcase, #projects, #announcements). Contribute value to the community before and after posting.

---

### YouTube / Loom

**Demo Video Script (2-3 minutes)**:

```
[0:00 - 0:15] Hook
"What if your AI agent could pick up the phone and make a call for you?
Today I'm going to show you call-use -- an open-source runtime that does
exactly that."

[0:15 - 0:45] The Problem
"AI agents can browse the web, write code, send emails. But there are
still thousands of tasks that require a phone call -- canceling
subscriptions, checking appointment times, navigating government phone
trees. Until now, agents couldn't do that."

[0:45 - 1:15] Live Demo -- Making a Call
[Screen recording of terminal]
"Here's call-use in action. I'm going to have an AI agent call [demo
number] and [task]. Watch."
[Show the call happening in real-time, with the agent navigating menus
and having a conversation]

[1:15 - 1:45] Code Walkthrough
"And here's how simple it is. Three lines of Python."
[Show code in editor with syntax highlighting]
"You create a CallAgent with a task and a phone number, and call
agent.call(). That's it."

[1:45 - 2:15] Key Features
"call-use also supports:"
- IVR navigation (show example)
- Human takeover (show taking over a call)
- Approval flow (show agent asking permission)
- 4 interfaces: SDK, CLI, MCP Server, REST API

[2:15 - 2:45] Architecture (Quick)
[Show architecture diagram]
"Under the hood, it uses LiveKit for real-time audio, Twilio for
telephony, GPT-4o for conversation, and Deepgram for speech-to-text."

[2:45 - 3:00] CTA
"call-use is open-source, MIT licensed, and available today.
pip install call-use. Link to GitHub in the description.
Star the repo if this is useful, and let me know what you'd build with it."
```

**Architecture Explainer Script (5 minutes)**: Deeper technical video covering the SIP bridging, LiveKit room architecture, STT/TTS pipeline, agent state machine, and how IVR detection works. Target audience: developers who want to contribute or understand the internals.

---

## Success Metrics

| Metric | Target (Week 1) | Stretch Goal |
|--------|-----------------|--------------|
| GitHub Stars | 500 | 1,000 |
| PyPI Installs | 200 | 500 |
| HN Points | 100 | 300 |
| Twitter Impressions | 50K | 200K |
| Product Hunt Upvotes | 100 | 300 |
| Contributors (PRs) | 3 | 10 |
| Discord/Community Members | 50 | 200 |
