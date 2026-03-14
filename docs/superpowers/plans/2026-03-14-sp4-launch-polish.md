# SP4: Launch Polish — GitHub Trending #1

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make call-use irresistible to star. Top-tier README, PyPI publish, demo recording, community launch.

**Architecture:** N/A — this is packaging, documentation, and distribution work.

**Tech Stack:** PyPI (twine), GitHub Actions (CI/CD), asciinema/GIF (demo recording)

---

## File Structure

```
README.md                          # REWRITE — viral-tier README
pyproject.toml                     # MODIFY — PyPI metadata, classifiers
.github/
├── workflows/
│   ├── ci.yml                     # CREATE — lint + test on PR
│   └── publish.yml                # CREATE — PyPI publish on tag
├── ISSUE_TEMPLATE/
│   ├── bug_report.md              # CREATE
│   └── feature_request.md         # CREATE
└── PULL_REQUEST_TEMPLATE.md       # CREATE
CONTRIBUTING.md                    # CREATE
CHANGELOG.md                       # CREATE
assets/
├── demo.gif                       # CREATE — hero demo recording
├── architecture.png               # CREATE — architecture diagram
└── social-preview.png             # CREATE — GitHub social preview (1280x640)
```

---

## Chunk 1: README Rewrite

### Task 1: Write viral-tier README

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Rewrite README**

Key sections (in order — every section must earn the reader's attention):

1. **Hero line + badge row**: One sentence + stars/PyPI/license badges
2. **Demo GIF**: 10-second recording of a real call (placeholder until we have it)
3. **What is this**: 3 sentences max. "browser-use for phones" analogy.
4. **Quickstart**: 4 lines of code. Must work with free tier (no infra setup).
5. **How it works**: Architecture diagram (clean, minimal)
6. **Features**: Table format, not bullet list. Compare vs building from scratch.
7. **Agent framework integrations**: Claude Code, LangChain, CrewAI, OpenAI Agents — 3 lines each
8. **Pine AI comparison**: Table showing call-use vs Pine AI
9. **Self-hosted setup**: For power users (Tier 3)
10. **API reference**: Brief, link to docs
11. **Contributing**: Link to CONTRIBUTING.md
12. **License**: MIT

Structure the README so that:
- First 5 seconds: reader knows what this is and sees it working (GIF)
- First 30 seconds: reader can try it themselves (quickstart)
- First 2 minutes: reader understands the full capability

```markdown
<div align="center">

# 📞 call-use

**Give your AI agent the ability to make phone calls.**

The [browser-use](https://github.com/browser-use/browser-use) for phones.

[![PyPI](https://img.shields.io/pypi/v/call-use)](https://pypi.org/project/call-use/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/agent-next/call-use)](https://github.com/agent-next/call-use/stargazers)

[Demo](#demo) · [Quickstart](#quickstart) · [Docs](#usage) · [Examples](#examples)

</div>

---

## Demo

<!-- Replace with actual recording -->
<div align="center">
<img src="assets/demo.gif" alt="AI agent cancels a cable subscription via phone" width="600">
<p><em>AI agent calls Comcast, navigates IVR, talks to a human, and cancels a subscription — autonomously.</em></p>
</div>

## Quickstart

```bash
pip install call-use
call-use auth --github          # Free tier: 5 calls/day to toll-free numbers
```

```python
from call_use import CallAgent

outcome = await CallAgent(
    phone="+18001234567",
    instructions="Cancel my internet subscription. Account #12345.",
).call()

print(outcome.disposition)   # "completed"
print(outcome.transcript)    # Full conversation transcript
```

Or from the CLI (any agent that can run bash can use this):

```bash
call-use dial "+18001234567" -i "Cancel my subscription" -u '{"account": "12345"}'
```

## What is this?

**call-use** is an open-source runtime that lets AI agents make outbound phone calls. Your agent dials a number, navigates IVR menus, talks to humans, and returns a structured result — just like [browser-use](https://github.com/browser-use/browser-use) lets agents browse the web.

## How it works

```
Your Agent (Claude, GPT, LangChain, ...)
    ↓  CallAgent.call() or CLI or MCP tool
call-use SDK
    ↓  LiveKit room + agent dispatch
call-use Worker (Deepgram STT → GPT-4o → OpenAI TTS)
    ↓  SIP trunk
Phone Network (PSTN)
    ↓
Human on the other end
```

## Features

| Feature | Description |
|---------|-------------|
| **Outbound calling** | Dial any US/Canada number via Twilio SIP |
| **IVR navigation** | Automatically press menu keys (DTMF) |
| **Natural conversation** | GPT-4o reasoning + OpenAI TTS voice |
| **Live transcript** | Real-time speech-to-text via Deepgram |
| **Approval flow** | Agent pauses for human approval on sensitive actions |
| **Human takeover** | Pause agent mid-call, take over with your voice |
| **Structured output** | JSON result with disposition, transcript, events |
| **Framework agnostic** | Works with any agent: Claude, GPT, LangChain, CrewAI |

## Use with any agent framework

### Claude Code (MCP)
```json
{"mcpServers": {"call-use": {"command": "call-use-mcp"}}}
```
Then: *"Call +18001234567 and cancel my subscription"*

### LangChain
```python
@tool
def phone_call(phone: str, instructions: str) -> str:
    result = subprocess.run(["call-use", "dial", phone, "-i", instructions], capture_output=True, text=True)
    return result.stdout
```

### OpenAI Agents SDK
```python
@function_tool
def phone_call(phone: str, instructions: str) -> str:
    result = subprocess.run(["call-use", "dial", phone, "-i", instructions], capture_output=True, text=True)
    return result.stdout
```

## Comparison

| | call-use | Pine AI | Build from scratch |
|---|---|---|---|
| Automated CS calls | ✅ | ✅ | 🔨 months |
| IVR navigation | ✅ | ✅ | 🔨 weeks |
| Human takeover | ✅ | ❌ | 🔨 weeks |
| Approval flow | ✅ | ✅ | 🔨 days |
| Open source | ✅ | ❌ | — |
| Self-hostable | ✅ | ❌ | — |
| Any agent framework | ✅ | ❌ | — |
| Setup time | **5 min** | signup + $$$ | **months** |
| Lines of code | **3** | — | **thousands** |
| Cost | free tier / self-host | $$$$ | $$$ |

## Three ways to run

| Tier | Setup | Limits | Best for |
|------|-------|--------|----------|
| **Free** | `call-use auth --github` | 5 calls/day, toll-free only | Trying it out |
| **Verified** | `call-use auth --phone` | Usage-based, any US number | Production agents |
| **Self-hosted** | Bring your own keys | Unlimited | Enterprise / full control |

## Self-hosted setup

<details>
<summary>Click to expand</summary>

### Prerequisites
- Python 3.11+
- LiveKit Cloud or self-hosted
- Twilio SIP trunk connected to LiveKit
- OpenAI API key + Deepgram API key

### Configure
```bash
export LIVEKIT_URL="wss://your-project.livekit.cloud"
export LIVEKIT_API_KEY="..."
export LIVEKIT_API_SECRET="..."
export SIP_TRUNK_ID="..."
export OPENAI_API_KEY="sk-..."
export DEEPGRAM_API_KEY="..."
```

### Run
```bash
pip install call-use
call-use-worker start    # Start the agent worker
call-use dial "+18001234567" -i "Ask about store hours"
```

</details>

## Examples

- [AI Refund Agent](examples/refund_agent/) — Pine AI in 50 lines
- [CS Agent](examples/cs_refund_agent.py) — Simple customer service call
- [LangChain integration](examples/langchain_tool.py)
- [OpenAI Agents integration](examples/openai_agents.py)
- [Claude Code MCP setup](examples/claude_code_setup.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
<strong>⭐ Star this repo if you want AI agents that can make phone calls.</strong>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for viral launch"
```

---

## Chunk 2: PyPI & CI

### Task 2: Update pyproject.toml for PyPI

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add PyPI metadata**

```toml
[project]
name = "call-use"
dynamic = ["version"]
description = "Give your AI agent the ability to make phone calls. The browser-use for phones."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
keywords = ["ai", "agent", "phone", "call", "voice", "livekit", "browser-use", "computer-use"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Communications :: Telephony",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

[project.urls]
Homepage = "https://github.com/agent-next/call-use"
Documentation = "https://github.com/agent-next/call-use#readme"
Repository = "https://github.com/agent-next/call-use"
Issues = "https://github.com/agent-next/call-use/issues"
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add PyPI metadata and classifiers"
```

---

### Task 3: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --tb=short

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check call_use/
      - run: ruff format --check call_use/
```

- [ ] **Step 2: Create publish workflow**

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/publish.yml
git commit -m "ci: add test/lint CI and PyPI publish workflows"
```

---

### Task 4: GitHub repo setup files

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `CONTRIBUTING.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Create issue templates**

```markdown
<!-- .github/ISSUE_TEMPLATE/bug_report.md -->
---
name: Bug Report
about: Report a bug
labels: bug
---

**What happened?**

**What did you expect?**

**How to reproduce**
1.
2.
3.

**Environment**
- call-use version:
- Python version:
- OS:
```

```markdown
<!-- .github/ISSUE_TEMPLATE/feature_request.md -->
---
name: Feature Request
about: Suggest a feature
labels: enhancement
---

**What problem does this solve?**

**Proposed solution**

**Alternatives considered**
```

- [ ] **Step 2: Create PR template**

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->
## What

## Why

## Test plan

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Linted (`ruff check call_use/`)
```

- [ ] **Step 3: Create CONTRIBUTING.md**

```markdown
# Contributing to call-use

## Setup
\```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
pytest
\```

## Development
- Write tests first
- Run `ruff check` and `ruff format` before committing
- One logical change per commit
- PR description should explain why, not just what

## Architecture
See the [README](README.md#how-it-works) for an overview.
```

- [ ] **Step 4: Create CHANGELOG**

```markdown
# Changelog

## [1.0.0] - 2026-03-XX

### Added
- CLI: `call-use dial` command for agent-native phone calls
- MCP server: native tool support for Claude Code, Codex
- Cloud: free tier with GitHub auth (5 calls/day to toll-free numbers)
- Cloud: verified tier with SMS phone binding
- Demo: AI Refund Agent (Pine AI in 50 lines)
- Framework examples: LangChain, OpenAI Agents, Claude Code

### Initial features (from 0.1.0)
- Python SDK: `CallAgent` for programmatic calls
- LiveKit-based voice agent with GPT-4o + Deepgram + OpenAI TTS
- Approval flow for sensitive actions
- Human takeover mid-call
- REST API for multi-tenant deployments
- JSON audit logs per call
```

- [ ] **Step 5: Commit**

```bash
git add .github/ CONTRIBUTING.md CHANGELOG.md
git commit -m "docs: add GitHub templates, contributing guide, and changelog"
```

---

## Chunk 3: Demo Recording & Assets

### Task 5: Record demo GIF

**Files:**
- Create: `assets/demo.gif`

- [ ] **Step 1: Set up recording environment**

Prerequisites:
- Working call-use setup (worker running)
- A toll-free number to call (e.g., airline, cable company)
- asciinema or VHS for terminal recording

- [ ] **Step 2: Record terminal demo**

Script to execute during recording:
```bash
# Show the install
pip install call-use

# Show the auth
call-use auth --github

# Make a real call
call-use dial "+18001234567" \
    -i "I'd like to cancel my subscription. Account number 12345." \
    -u '{"name": "Alice Chen", "account": "12345"}'
```

- [ ] **Step 3: Convert to GIF and add to assets/**

```bash
# Using VHS
vhs demo.tape  # Outputs demo.gif
mv demo.gif assets/demo.gif
```

- [ ] **Step 4: Commit**

```bash
git add assets/demo.gif
git commit -m "docs: add demo GIF for README"
```

---

### Task 6: Create architecture diagram

**Files:**
- Create: `assets/architecture.png`

- [ ] **Step 1: Generate architecture diagram**

Use the draw.io skill or create a clean SVG/PNG showing:
```
Your Agent → call-use SDK → LiveKit → Worker → SIP → Phone
```

- [ ] **Step 2: Commit**

```bash
git add assets/architecture.png
git commit -m "docs: add architecture diagram"
```

---

## Chunk 4: Quality — Best Models, Best Performance

### Task 7: Upgrade to best-in-class models

**Files:**
- Modify: `call_use/agent.py`

V1 prioritizes quality over cost. Use the best available models:

- [ ] **Step 1: Update model selection in agent.py**

```python
# In _LiveKitCallAgent.run():
session = AgentSession(
    stt=deepgram.STT(model="nova-3", language="en-US"),
    llm=openai.LLM(model="gpt-4o"),           # Best reasoning for call navigation
    tts=openai.TTS(model="gpt-4o-mini-tts", voice=tts_voice),  # Best voice quality
    vad=silero.VAD.load(),
    turn_detection="vad",
    min_endpointing_delay=0.6,
)
```

Note: Current models are already top-tier:
- STT: Deepgram nova-3 (best real-time STT)
- LLM: GPT-4o (best reasoning)
- TTS: GPT-4o-mini-TTS (best voice quality at speed)
- VAD: Silero (best open-source VAD)

If newer/better models are available at launch time, update here.

- [ ] **Step 2: Verify no cost-optimization shortcuts exist**

Review agent.py for any quality-compromising patterns:
- No model downgrades for "cheaper" operation
- No reduced context windows
- No audio quality degradation
- Krisp noise cancellation enabled (already is)

- [ ] **Step 3: Commit if any changes made**

```bash
git add call_use/agent.py
git commit -m "perf: ensure best-in-class models for v1 launch"
```

---

### Task 8: PyPI publish dry run

- [ ] **Step 1: Build the package**

Run: `python -m build`
Expected: Creates `dist/call_use-1.0.0.tar.gz` and `.whl`

- [ ] **Step 2: Check package**

Run: `twine check dist/*`
Expected: PASSED

- [ ] **Step 3: Test install from wheel**

```bash
pip install dist/call_use-*.whl
call-use --version
call-use dial --help
```
Expected: All commands work

- [ ] **Step 4: Tag and publish**

```bash
git tag -a v1.0.0 -m "call-use v1.0.0 — the browser-use for phones"
git push origin v1.0.0  # Triggers publish.yml
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Viral-tier README rewrite |
| 2 | PyPI metadata + classifiers |
| 3 | CI/CD workflows (test + publish) |
| 4 | GitHub templates + contributing guide |
| 5 | Demo GIF recording |
| 6 | Architecture diagram |
| 7 | Best-in-class model verification |
| 8 | PyPI publish |

**Total: 8 tasks, ~10 commits**
