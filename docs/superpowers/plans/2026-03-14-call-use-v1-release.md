# call-use v1.0 Release Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship call-use as a top-tier open-source project — the "browser-use for phone calls" — with zero-friction onboarding, agent-native interfaces, and a killer demo app that rivals Pine AI.

**Architecture:** Four independent sub-projects, each producing a shippable increment. CLI and MCP server wrap the existing SDK. Cloud backend adds hosted infrastructure for Tier 1/2. Demo app proves the value proposition.

**Tech Stack:** Python 3.11+, LiveKit Agents v1.4, FastAPI, Twilio SIP, Deepgram STT, OpenAI GPT-4o/TTS, Click (CLI), MCP SDK

---

## Sub-Project Overview

```
Sub-Project 1: CLI + MCP Server (agent-native interfaces)
    ↓ enables
Sub-Project 2: Cloud Backend (Tier 1 & 2 onboarding)
    ↓ enables
Sub-Project 3: Demo App — "AI Refund Agent" (Pine AI killer)
    ↓ packaged with
Sub-Project 4: Launch Polish (README, PyPI, demo GIF, landing page)
```

Each sub-project gets its own plan, own PR, own release cycle.

---

## Sub-Project 1: CLI + MCP Server

**Goal:** Any AI agent that can run bash or connect to MCP can use call-use with one command.

**Deliverables:**
- `call-use dial` CLI command
- `call-use auth` CLI command (for Tier 1/2, stubbed in SP1)
- MCP server with `dial`, `status`, `cancel` tools
- Framework integration docs (LangChain, CrewAI, OpenAI Agents)

**Plan:** `2026-03-14-sp1-cli-mcp.md`

---

## Sub-Project 2: Cloud Backend (Tier 1 & 2)

**Goal:** `pip install call-use && call-use dial` works without any infrastructure setup.

**Deliverables:**
- call-use cloud API (hosted FastAPI + LiveKit + Twilio)
- Tier 1: Free sandbox number, 800-number only, 5 calls/day, GitHub OAuth
- Tier 2: SMS phone verification, bind own caller ID, usage-based
- Tier 3: Self-hosted (already works)
- API key management, rate limiting, abuse prevention

**Plan:** `2026-03-14-sp2-cloud-backend.md`

**Dependencies:** SP1 (CLI `auth` command connects to cloud)

---

## Sub-Project 3: Demo App — AI Refund Agent

**Goal:** A complete application that does what Pine AI does, built in <100 lines on call-use. Proves that a VC-funded startup's entire product can be built on our SDK in an afternoon.

**Deliverables:**
- `examples/refund_agent/` — full working refund agent
- Web UI: user enters "Cancel my Comcast, account #12345" → agent calls → live transcript → result
- CLI mode: `call-use-demo refund "+18001234567" "Cancel subscription, account 12345"`
- Video/GIF recording of a real call for README
- Blog post / Twitter thread material

**Plan:** `2026-03-14-sp3-demo-app.md`

**Dependencies:** SP1 (uses CLI/SDK), SP2 (demo uses free tier for zero-setup experience)

---

## Sub-Project 4: Launch Polish

**Goal:** GitHub Trending #1 in Python. Make the repo irresistible to star.

**Deliverables:**
- README rewrite: hero GIF, 3-line quickstart, comparison table (call-use vs Pine AI vs building from scratch)
- PyPI publish (`pip install call-use`)
- GitHub repo setup: topics, description, social preview image
- `.github/`: issue templates, contributing guide, CI badges
- Landing page (optional): calluse.dev
- Launch plan: HN, Twitter/X, Reddit r/MachineLearning, Discord communities

**Plan:** `2026-03-14-sp4-launch-polish.md`

**Dependencies:** SP1 + SP2 + SP3 complete

---

## Execution Order

```
Week 1-2:  SP1 (CLI + MCP) — foundation for everything else
Week 2-3:  SP2 (Cloud Backend) — enables zero-friction onboarding
Week 3-4:  SP3 (Demo App) — killer demo built on SP1+SP2
Week 4:    SP4 (Launch Polish) — package everything for launch
```

## Success Criteria

- [ ] `pip install call-use && call-use dial "+18001234567" --instructions "Ask hours"` works end-to-end
- [ ] Claude Code can `mcp__call_use__dial(phone, instructions)` natively
- [ ] Free tier: zero config, zero cost for first 5 calls/day to 800 numbers
- [ ] Demo GIF in README shows a real AI-driven refund call
- [ ] <100 lines to build a Pine AI competitor
- [ ] GitHub: 1000+ stars in first week (stretch goal)
