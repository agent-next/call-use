# Call-Use PRD v2.1

_Revised from v1 → v2 → v2.1. v2 resolved all 6 HIGH (H1-H6), 7 MEDIUM (M1-M7), 2 LOW (L1-L2), and 4 CC-supplementary (CC1-CC4) findings. v2.1 addresses 2 new HIGH, 2 new MEDIUM, 1 new LOW from CX re-review, and 1 MEDIUM + 5 LOW from CC re-review._

---

## 1. Product Definition

### One line

**Call-Use is an open-source outbound call-control runtime for agent builders.**

### Expanded

Call-Use gives AI agents the ability to make phone calls and execute tasks through voice conversations. It handles dialing, voice interaction, IVR navigation, hold detection, human handoff, and evidence collection — so application agents don't have to.

It is not a vertical product (no built-in refund/booking/insurance logic). It is not a telephony wrapper (it adds agent-level semantics on top of raw telephony). It is an **execution layer** that sits between upper-layer orchestrators and lower-layer telephony/voice providers.

### Analogy and its limits

Call-Use is inspired by browser-use and computer-use — agent execution layers for web and desktop. The analogy holds directionally: all three give agents a channel to interact with the real world.

**Where the analogy breaks down** (and we acknowledge this explicitly):

* Browser-use wraps a deterministic, inspectable DOM. Phone calls are partially observable, non-deterministic voice conversations with humans and automated systems.
* Browser actions are replayable and verifiable. Phone call outcomes depend on the other party and cannot be replayed.
* Browser-use can screenshot state. Phone state must be inferred from audio, which is lossy.

This means Call-Use cannot offer browser-like determinism. It offers **best-effort execution with structured evidence** — transcripts, event logs, and outcome reports that let the upper layer verify what happened.

---

## 2. Product Positioning

### We are

* An open-source outbound call-control runtime
* Initially optimized for human-service calls (CS, booking, cancellation)
* A Python SDK + API for agent builders
* BYO-provider, local-first, auditable

### We are not

* A consumer product
* A vertical business agent
* An enterprise call center
* A full voice-assistant platform (unlike Vapi/Retell)
* A pure telephony API wrapper

### Where we sit

```
┌─────────────────────────────────────────────┐
│  Application Agents                         │
│  (refund bot, booking bot, cancellation bot) │
├─────────────────────────────────────────────┤
│  Call-Use  ← you are here                   │
│  (call control, voice interaction, evidence) │
├─────────────────────────────────────────────┤
│  Providers                                  │
│  (LiveKit + Twilio, Deepgram, OpenAI, etc.) │
└─────────────────────────────────────────────┘
```

Upper layers decide **why** to call, **whom** to call, and **what** the goal is. Call-Use executes the call and returns evidence.

---

## 3. Vision

### Long term

Become the standard open-source runtime for agent-initiated phone calls — the way browser-use is becoming the standard for agent-initiated web browsing.

### Medium term

Let any agent framework (Claude Code, OpenAI Agents SDK, LangChain, CrewAI) add phone-call capability via `pip install call-use`.

### Short term (v1)

Ship a working Python SDK + REST API that can:
1. Dial a US phone number
2. Navigate IVR menus
3. Have a voice conversation guided by a task prompt
4. Stream events (transcript, state changes) to the caller
5. Pause for human approval or handoff
6. Return a structured evidence bundle

---

## 4. Problem

Agents can browse the web, control computers, call APIs, read files, and search email. But many real-world tasks still require a phone call:

* Refunds, cancellations, disputes
* Appointments, reservations, rescheduling
* Account inquiries, verification, follow-ups
* Any process where a company only offers phone support

The problem is not lack of telephony or voice models. The problem is:

**No standard execution layer translates an agent's intent into a completed phone call and returns structured evidence.**

Today an agent builder who wants phone capability must wire together: SIP dialing, audio streams, STT, LLM, TTS, DTMF, hold detection, turn-taking, human handoff, and result extraction. That's too much.

---

## 5. Goals and Non-Goals

### Goals

1. Provide a Python SDK that abstracts outbound call execution
2. Let upper layers remain ignorant of SIP, audio frames, and carrier details — **with explicit acknowledgment of what leaks through** (see Section 9)
3. Support human-in-the-loop: approval gates and live takeover
4. Return structured evidence (transcript, events, outcome summary)
5. Be open-source, BYO-provider, local-runnable
6. Ship one excellent interface (SDK/API) before expanding to others

### Non-Goals

1. No built-in vertical business logic
2. No consumer-facing product
3. No inbound call handling in v1 (fundamentally different routing/auth/abuse model)
4. No multi-provider abstraction in v1 (honestly: v1 binds to LiveKit + Twilio)
5. No commercial monetization in v1

---

## 6. Target Users

### Primary: Agent builders / developers

People who already have an agent and want to give it phone capability.

* Claude Code / OpenAI Agents SDK users
* LangChain / CrewAI workflow builders
* AI product teams building vertical agents
* Indie hackers automating personal tasks

Core need: **"I have an agent. I want it to make a phone call and tell me what happened."**

### Secondary: Vertical product teams

Teams building refund agents, booking agents, cancellation agents, etc. They don't want to build a call runtime; they want to import one.

### End users

End users never see Call-Use. They see: "My AI handled the phone call for me."

---

## 7. Core Value Propositions

| Audience | Value |
|----------|-------|
| Developers | Add phone capability to any agent in <100 lines of code |
| Product teams | Skip 2-3 months of telephony plumbing |
| End users | Phone tasks that required 30 min of hold music now run in the background |
| Ecosystem | A standard phone-execution primitive that composes with web-use and computer-use |

---

## 8. Core Capabilities

Organized around **phone execution primitives**, not business scenarios.

### A. Call Session

Manages outbound call lifecycle:

* Dial a phone number with optional caller ID
* Monitor call state (dialing → connected → ended; `ringing` requires SIP progress events not exposed by LiveKit — deferred until provider support available)
* Hang up
* Detect call failure (busy, no answer, carrier reject, mid-call drop)
* Retry policy (configurable by upper layer)

_v1 scope: outbound only. Inbound, transfer, and conference are future._

### B. Call Navigation

Handles automated phone systems:

* Detect IVR prompts (heuristic: "Press X for..." patterns in transcript)
* Send DTMF tones
* Detect hold (music/silence/periodic prompts)
* Detect voicemail greeting
* Detect transfer to a new party

_These are best-effort detections based on audio/transcript analysis, not guaranteed classifications._

### C. Voice Interaction

Real-time voice conversation:

* STT: transcribe what the other party says
* LLM: generate appropriate responses based on task instructions
* TTS: speak the response
* Turn-taking: VAD-based endpointing
* Streaming transcript to upper layer

### D. Human Handoff

Two mechanisms for human involvement:

* **Approval gate**: Agent pauses, asks upper layer for approval before committing to something (e.g., accepting a refund offer). Upper layer approves/rejects. Agent resumes.
* **Live takeover**: Human takes over the phone call directly (agent muted, human speaks). Human resumes agent when done.

_The specific scenarios that trigger handoff (OTP, identity verification, financial commitment) are configured by the upper layer via task instructions, not hardcoded in the runtime._

### E. Evidence Collection

Raw evidence returned to upper layer after every call:

* **Transcript**: timestamped turns `[{speaker, text, timestamp}]`
* **Event log**: state changes, DTMF presses, hold periods, handoff events
* **Call metadata**: duration, participants, disposition (completed/failed/no-answer/voicemail)
* **Audio recording** (optional, if enabled — v1 deferred, see Section 12)

_Domain-specific extraction (case numbers, ETAs, confirmation codes) is NOT a runtime responsibility. Upper layers can extract these from the raw transcript. We may ship optional extractors as plugins/examples, but they are not core._

**Current implementation gap**: The existing codebase has audit log scaffolding (`audit.py`) with methods for transcript/DTMF/LLM events, but these are not yet called from the agent. Call logs show empty `events: []`. Phase 1 must wire STT output, LLM responses, and DTMF actions into the event pipeline. This is new development, not claimed as existing.

### F. Voice Configuration

TTS voice is configurable:

* Default: provider's standard voice (e.g., OpenAI "alloy")
* Custom: any TTS voice ID supported by the configured provider

_Voice cloning and branded voices are product-level features with legal/compliance implications. They are supported by passing the appropriate voice ID, but Call-Use does not manage voice creation, storage, or consent._

---

## 9. Abstraction Boundaries — What Leaks

We aim to hide telephony complexity, but some things necessarily leak to the upper layer. Being explicit about this prevents false expectations.

### Hidden by Call-Use (upper layer doesn't see)

* SIP signaling
* Audio frame encoding/decoding
* WebRTC/RTP transport
* STT/TTS provider protocol details
* LiveKit room management
* DTMF tone generation

### Exposed to upper layer (must be aware of)

| Leaked concern | Why it leaks | How we handle it |
|---------------|-------------|-----------------|
| Caller ID | Carriers require a verified number; affects answer rates | Upper layer provides caller_id in task config |
| Phone number format | E.164, country restrictions, carrier rules | SDK validates; returns clear errors |
| Recording consent | Two-party consent states require disclosure | Upper layer responsible for compliance; SDK provides a `recording_disclaimer` config |
| Call cost | SIP minutes + STT + LLM + TTS are real costs | BYO credentials; cost is transparent |
| Non-determinism | Same call twice may produce different outcomes | Evidence bundle lets upper layer verify |
| Latency | Voice conversations have hard real-time constraints | SDK manages; upper layer sees transcript delay |
| Carrier restrictions | Spam labeling, STIR/SHAKEN, TCPA | See Section 16 (Risks) |

---

## 10. Unified Object Model

All interfaces (SDK, API, CLI) use the same core objects:

### CallTask

```
task_id: str
phone_number: str          # E.164 format
caller_id: str | None      # Verified number
instructions: str          # What to accomplish
user_info: dict            # Context to use during call
voice_id: str | None       # TTS voice override
approval_required: bool    # Whether to pause for binding decisions
timeout_seconds: int       # Max call duration
```

### CallState

```
state: enum {
  created,
  dialing,
  ringing,
  connected,        # Someone picked up
  in_ivr,           # Navigating automated menu (best-effort detection)
  on_hold,          # Waiting (best-effort detection)
  in_conversation,  # Talking to a human (best-effort detection)
  awaiting_approval,# Paused for human decision
  human_takeover,   # Human has taken over
  ended
}
disposition: enum {completed, failed, no_answer, busy, voicemail, timeout, cancelled}
```

**Mapping from current codebase to target states:**

| Current state (`cs_agent.py`) | Target state(s) | Implementation needed |
|-------------------------------|-----------------|----------------------|
| _(no state before connect)_ | created, dialing | New: track SIP call progress. `ringing` defined in enum but not emitted in v1 (LiveKit SIP does not expose 180 Ringing to agent process) |
| `active` | connected, in_ivr, on_hold, in_conversation | New: audio classification to distinguish sub-states within `active` |
| `awaiting_approval` | awaiting_approval | Exists — direct mapping |
| `paused` | human_takeover | Exists — rename |
| _(on disconnect)_ | ended | Exists — expand with disposition logic |

_Note: `in_ivr`, `on_hold`, and `in_conversation` are best-effort classifications derived from transcript/audio heuristics. They may be inaccurate. The runtime always provides the raw evidence (transcript, events) so upper layers can make their own determination._

### CallEvent

```
timestamp: float
type: enum {
  state_change,     # State transition
  transcript,       # Someone spoke
  dtmf,             # Key pressed
  approval_request, # Agent needs approval
  approval_response,# Upper layer responded
  takeover,         # Human took over
  resume,           # Agent resumed
  error,            # Something went wrong
  call_complete     # Call ended — data contains full CallOutcome
}
data: dict          # Type-specific payload
```

### CallOutcome

```
task_id: str
transcript: list[Turn]     # [{speaker, text, timestamp}]
events: list[CallEvent]
duration_seconds: float
disposition: str           # From CallError taxonomy or "completed"
recording_url: str | None  # v1: deferred (None); v2+: optional
metadata: dict             # Provider-specific extras
```

_Note: There is no `success` field. Whether the task succeeded is a domain judgment that belongs to the upper layer. Call-Use provides raw evidence; the upper layer determines success by analyzing the transcript and events._

### Failure taxonomy

```
CallError:
  dial_failed:      # Could not connect (bad number, carrier reject)
  no_answer:        # Rang but nobody picked up
  busy:             # Line busy
  voicemail:        # Reached voicemail (auto-detected)
  mid_call_drop:    # Call dropped unexpectedly
  timeout:          # Exceeded max duration
  provider_error:   # LiveKit/Twilio/STT/LLM service error
  rate_limited:     # Too many calls
  cancelled:        # Upper layer cancelled
```

---

## 11. Usage Patterns

### SDK (primary interface for v1)

```python
from call_use import CallAgent

agent = CallAgent(
    phone="+18001234567",
    instructions="Cancel my internet subscription. Account number 12345.",
    user_info={"name": "Alice Smith", "account": "12345"},
    on_event=lambda e: print(e),         # Real-time events
    on_approval=lambda details: "approved",  # Auto-approve (or ask human)
)
outcome = await agent.call()

print(outcome.transcript)
print(outcome.disposition)
```

### REST API (secondary interface for v1)

```
POST /calls          → Create + start call (returns room_name + livekit_token for monitoring)
GET  /calls/{id}     → Get current state + participants
POST /calls/{id}/approve  → Approve pending decision
POST /calls/{id}/reject   → Reject pending decision
POST /calls/{id}/takeover → Human takes over
POST /calls/{id}/resume   → Resume agent
POST /calls/{id}/cancel   → Cancel call
```

_Real-time event streaming uses LiveKit's native data channel on the `call-events` topic. The `livekit_token` returned at call creation allows clients to join the room as a subscribe-only monitor. This avoids building a custom WebSocket forwarding layer and leverages LiveKit's existing real-time infrastructure._

### Upper layer does NOT see

* SIP, audio frames, room metadata, participant permissions
* Provider-specific configuration (handled in CallAgent init or env vars)

### Upper layer MUST handle

* Task instructions (what to accomplish)
* Approval decisions (approve/reject binding commitments)
* Compliance (recording consent, TCPA, caller ID legitimacy)
* Domain-specific outcome extraction (parse transcript for case numbers, etc.)

---

## 12. MVP Scope

**Principle: One interface done excellently, not five done poorly.**

### MVP must have

1. **Python SDK** (`pip install call-use`) — the primary interface
2. **Outbound dialing** to US/CA numbers via LiveKit + Twilio
3. **Voice conversation** using Deepgram STT + configurable LLM + configurable TTS
4. **IVR/DTMF navigation** (best-effort detection + key sending)
5. **Event streaming** via callback (SDK) and LiveKit data channel subscription (API)
6. **Approval gate** (pause/approve/reject)
7. **Human takeover/resume**
8. **Evidence bundle** (transcript, events, metadata) returned on completion
9. **REST API** alongside SDK (same server process)
10. **One working example**: a CS refund agent built on top of call-use (in `examples/`)

### MVP must NOT have

* MCP server, Skill, or CLI wrapper (these are Phase 2 adapters)
* Multi-provider abstraction (v1 = LiveKit + Twilio, honestly)
* Inbound call support
* Voice cloning management
* Dashboard or monitoring UI
* Domain-specific outcome extractors in core (ship as example only)
* Enterprise features (multi-tenant, billing, admin)

### What we reuse from current codebase

| Current asset | Reuse in v1 |
|--------------|-------------|
| SIP dialing via LiveKit + Twilio | Yes — proven, keep |
| Deepgram STT + OpenAI LLM + TTS pipeline | Yes — proven, keep |
| VAD-based turn detection (0.6s) | Yes — proven, keep |
| State machine (active/paused/awaiting_approval) | Yes — extract and generalize |
| Dual-lock pattern (_cmd_lock + _reply_lock) | Yes — proven concurrency model |
| Approval ID correlation | Yes — proven, keep |
| FastAPI endpoints | Refactor — same semantics, new schema |
| Agent instructions (CS-specific) | Move to `examples/` — not in core |
| Audit log (JSON) | Evolve into CallOutcome evidence bundle (same on-disk JSON, richer schema) |
| Phone validation (NANP denylist) | Keep in SDK, improve |

### What requires new development

* Python SDK package structure (`call_use/`)
* CallTask / CallState / CallEvent / CallOutcome data models
* Wire STT/LLM/DTMF events into evidence pipeline (currently scaffolded but uncalled)
* LiveKit monitor token generation for event subscription
* Failure detection and disposition mapping (busy, no-answer, voicemail, mid-call drop)
* Cancel endpoint (`POST /calls/{id}/cancel`)
* Rate limiting middleware
* Caller ID validation (verify ownership before dialing)
* State mapping: expand 3-state (active/paused/awaiting_approval) → 10-state model
* Generic agent instructions (task-driven, not CS-hardcoded)
* Package publishing pipeline (PyPI)
* README and quickstart docs
* Example: refund agent built on call-use

### Explicitly deferred to Phase 2+

* Audio recording storage and retrieval
* Retry policy (upper layer retries by creating a new CallTask in v1)
* In-memory call registry → persistent storage (v1 accepts state loss on restart as known limitation)

---

## 13. Provider Binding (Honest Statement)

### v1 reality

v1 is bound to specific providers:

| Layer | Provider | Why |
|-------|----------|-----|
| Telephony | LiveKit SIP + Twilio | Only stack we've validated end-to-end |
| STT | Deepgram Nova-3 | Best price/quality for telephony |
| LLM | OpenAI GPT-4o (via LiveKit `openai.LLM()` plugin) | Other OpenAI-compatible endpoints may work but are untested |
| TTS | OpenAI GPT-4o-mini-TTS (via LiveKit `openai.TTS()` plugin) | Other OpenAI-compatible TTS may work but are untested |
| VAD | Silero | LiveKit default, proven |

### v2+ aspiration

Abstract provider interfaces so community can add:
* Alternative SIP providers (Vonage, Telnyx)
* Alternative STT (Whisper, AssemblyAI)
* Alternative LLM (Claude, Gemini)
* Alternative TTS (ElevenLabs, PlayHT)

But v1 ships with what works today. We don't pretend to be provider-agnostic before we are.

---

## 14. Security and Abuse Model

### Exists today (proven in current codebase)

| Concern | Current mitigation |
|---------|-------------------|
| Who can dial | API key auth via `X-API-Key` header (`server/main.py:51`) |
| What numbers | US/CA NANP validation, E.164 fullmatch, NPA denylist, premium/toll block (`server/main.py:97-124`) |
| PII safety | Agent instructions prohibit SSN, full CC, passwords (`cs_agent.py:79`) |
| Abuse forensics | Per-call JSON audit log written on successful SIP disconnect (`audit.py`). **Limitation**: logs currently have empty `events[]` (event wiring is scaffolded but uncalled); logs are not written if call setup fails or agent crashes before disconnect. Must-build items below address these gaps. |

### Must build for v1 launch

| Concern | Required mitigation | Status |
|---------|--------------------|--------|
| Rate limiting | Configurable per-API-key rate limit (default 10 calls/hour) | Not implemented |
| Caller ID format validation | Validate caller_id is valid E.164 NANP format before dialing | Not implemented |
| Recording consent | SDK `recording_disclaimer` config that injects consent language into agent instructions | Not implemented |
| STIR/SHAKEN | Ensure Twilio trunk has proper attestation level configured | Config check needed |
| Prompt injection via voice | Explicit LLM system prompt guardrails treating STT output as untrusted | Partially exists in instructions |

### Deferred to v2 (acknowledged limitations)

| Concern | Why deferred | v1 mitigation |
|---------|-------------|---------------|
| Caller ID ownership verification | Requires Twilio Lookup API integration; format validation + STIR/SHAKEN attestation provide partial protection in v1 | Format-only validation + trunk-level STIR/SHAKEN |
| Configurable PII policy | v1 hardcodes "never provide SSN/CC/passwords" in base prompt; configurable policy requires schema design | Hardcoded base prompt guardrails |

### Not addressed in v1

* Per-user identity verification (v1 trusts API key holder)
* International dialing (complex regulatory landscape)
* Multi-tenant isolation
* Real-time abuse detection

---

## 15. Success Criteria

### For developers

* `pip install call-use` → working in 5 minutes
* Read README → understand product in 5 minutes
* Run example → complete first real call in 30 minutes
* Total time to integrate: < 1 hour for basic use case

### For the project

* 500+ GitHub stars within 3 months of launch
* 10+ community-contributed examples/adapters within 6 months
* Referenced in agent framework docs (LangChain, CrewAI, etc.)
* "call-use" becomes a recognized term in agent builder community

---

## 16. Risks

### Product risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Becomes "another voice app" | HIGH | Strict scope discipline; no vertical logic in core |
| Becomes telephony wrapper | HIGH | Agent-level semantics (task, evidence, approval) differentiate |
| Interface too heavy | HIGH | Ship SDK-first; keep surface small |
| Scope creep to inbound/multi-provider | MEDIUM | Explicit non-goals; say no until v2 |
| Browser-use analogy misleads expectations | MEDIUM | Honest "limits of the analogy" section in README |

### Technical risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Carrier spam labeling kills answer rates | HIGH | STIR/SHAKEN via Twilio; verified caller ID |
| TCPA/robocall compliance | HIGH | Human-initiated only; audit trail; legal review before launch |
| STT errors cause wrong actions | MEDIUM | Transcript is evidence; upper layer can verify |
| LLM hallucinates during call | MEDIUM | Approval gates for binding decisions; instructions guard rails |
| Mid-call state recovery | MEDIUM | v1: no recovery (call fails); v2: reconnect logic |
| No replay/eval harness | MEDIUM | Call recording is Phase 2+; v1 relies on transcript evidence; eval framework in Phase 3 |
| Voice prompt injection | LOW | LLM treats callee speech as untrusted; instructions include defense |

### Business risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| AI voice impersonation regulation | HIGH | Monitor regulatory landscape; default synthetic voice |
| Recording consent by jurisdiction | MEDIUM | Upper layer responsibility; SDK provides tools |
| Provider dependency (LiveKit + Twilio) | MEDIUM | v1 accepts this; v2 abstracts |
| Open-source sustainability | LOW | No premature monetization; focus on community first |

---

## 17. Competitive Positioning

### Why not Vapi or Retell?

Vapi and Retell are excellent voice-AI platforms. They serve overlapping developer audiences. Our differentiation is specific and narrow:

| Dimension | Vapi / Retell | Call-Use |
|-----------|--------------|----------|
| Model | Hosted platform, API-first | Open-source, local-first, BYO-everything |
| Control | Configure via dashboard/API | Full code control — you own the runtime |
| Pricing | Per-minute platform fees | Zero platform cost (BYO provider accounts) |
| Human handoff | Basic transfer/handoff | First-class approval gates + live takeover with continuity |
| Evidence | Transcript + recording | Structured evidence bundle (transcript + events + metadata); recording in Phase 2 |
| Agent integration | SDK for their platform | SDK designed to be called by any agent framework |
| Lock-in | Vendor lock-in | Open-source — fork code, modify anything; v1 binds LiveKit+Twilio, v2+ abstracts providers |

**Our wedge: open-source, BYO-provider, agent-native, evidence-first.**

We don't try to compete on hosted ease-of-use. We compete on control, transparency, and composability.

### Adjacent products (not competitors)

* **Pine / DoNotPay**: Vertical consumer products built on top of call capability. They validate demand. They could be built on Call-Use.
* **LiveKit / Twilio**: Infrastructure providers. We build on them. We are complementary.

### True reference point

* **browser-use**: Open-source agent web-execution layer. Directional inspiration, not literal model.
* **computer-use**: Anthropic's agent desktop-execution capability. Same spirit, different medium.

---

## 18. Development Roadmap

### Phase 1: Core Runtime (current)

* Python SDK package (`call_use/`)
* CallTask / CallState / CallEvent / CallOutcome models
* Outbound dialing (LiveKit + Twilio)
* Voice conversation (Deepgram + OpenAI)
* IVR/DTMF, hold detection
* Event streaming (SDK callback + LiveKit data channel)
* Approval gate + human takeover
* Evidence collection
* REST API
* One example (CS refund agent)
* README + quickstart
* PyPI publish

### Phase 2: Ecosystem + Recording

* MCP server
* Claude Code skill
* CLI wrapper
* LangChain / CrewAI tool adapters
* Call recording storage and retrieval
* More examples (booking, cancellation, inquiry)
* Community contribution guide

### Phase 3: Maturity

* Provider abstraction (swap Twilio, swap STT, etc.)
* Inbound call support
* Replay/eval harness (requires recording from Phase 2)
* Optional domain extractors (plugin system)
* Improved hold/voicemail/transfer detection

### Phase 4: Scale

* Hosted option
* Multi-tenant
* Enterprise features
* Commercial model (if warranted)

---

## 19. Open Source Strategy

### Principles

1. **README is the product** — if README isn't clear, nothing else matters
2. **5-minute quickstart** — clone, install, make a call
3. **BYO everything** — user provides their own API keys for all providers
4. **No hidden services** — runtime runs entirely on user's machine
5. **Permissive license** (MIT or Apache 2.0)
6. **Examples over docs** — working examples > pages of documentation

### Initial launch target

Form the mental model: **"Call-Use = phone execution layer for agents"**

Not "the phone version of browser-use" (too literal, analogy breaks down). Instead: **"What browser-use did for web browsing, Call-Use does for phone calls — but adapted to the fundamentally different nature of voice conversations."**

---

## 20. Final Product Definition

**Call-Use is an open-source outbound call-control runtime for agent builders.**

It lets AI agents make phone calls, navigate IVR systems, have voice conversations, pause for human approval, and return structured evidence — all through a simple Python SDK.

v1 runs on LiveKit + Twilio with Deepgram STT and OpenAI LLM/TTS. It ships as `pip install call-use` with a REST API, LiveKit data-channel event streaming, and one working example.

It does not contain vertical business logic. It does not pretend to abstract away all telephony complexity. It provides the best execution layer it can, with honest evidence of what happened, and lets upper-layer agents make the decisions.

---

## Appendix A: Revision History

### v1 → v2 (CC + CX review round 1)

| Issue | Resolution |
|-------|-----------|
| H1: CS-specific items in core capabilities | Moved to upper layer / examples / plugins |
| H2: browser-use analogy overstated | Added "limits of analogy" section; honest framing |
| H3: "hide telephony" infeasible | Added Section 9 (What Leaks) — explicit about what's exposed |
| H4: MVP too large | Cut to SDK + API only; adapters are Phase 2 |
| H5: Rewrite cost unclear | Added reuse table in Section 12 |
| H6: Vapi/Retell differentiation weak | Rewrote Section 17 with specific dimension comparison |
| M1: Abstract model too thin | Added full object model with failure taxonomy (Section 10) |
| M2: Structured outcome overclaimed | Renamed to Evidence Collection; domain extraction is upper layer |
| M3: Voice Identity in wrong layer | Reduced to "voice configuration" — pass voice_id, no management |
| M4: No event streaming | Added LiveKit data-channel + SDK callback as v1 requirement |
| M5: Design drift | Acknowledged; v1 uses OpenAI TTS, not ElevenLabs |
| M6: Risk blind spots | Added full risk tables (product, technical, business) |
| M7: Inbound in core | Explicitly excluded from v1; listed as Phase 3 |
| L1: "Four things" = five | Fixed |
| L2: Takeover surface undefined | SDK callback + API endpoint; no UI in v1 |
| CC1: No failure model | Added failure taxonomy in object model |
| CC2: No cost model | Added BYO-provider cost transparency |
| CC3: Provider binding dishonest | Added Section 13 (honest provider binding) |
| CC4: No security/abuse model | Added Section 14 (security and abuse model) |

### v2 → v2.1 (CX re-review + CC new findings)

| Issue | Resolution |
|-------|-----------|
| CX-NEW-H1: Evidence/event promises not grounded in code | Added implementation gap callout in Section 8E; new-dev list in Section 12 includes wiring events |
| CX-NEW-H2: Security day-1 overstates current state | Split Section 14 into "exists today" vs "must build for v1 launch" |
| CX-NEW-M1: State model not mapped to current code | Added mapping table in Section 10 (CallState) |
| CX-NEW-M2: Audit log vs CallOutcome inconsistency | Clarified as evolution (same on-disk JSON, richer schema) |
| CX-NEW-L1: "8 HIGH" count mismatch | Fixed header text |
| CC-N1: CallOutcome.success ambiguous | Removed `success` field; upper layer determines from evidence |
| CC-N2: Retry policy unspecified | Clarified: v1 defers retry; upper layer creates new CallTask |
| CC-N3: Event stream auth unspecified | Added token-based auth note in Section 11 (LiveKit monitor token) |
| CC-N4: "OpenAI-compatible" overclaimed | Qualified in Section 13 provider table |
| CC-N5: Recording implementation unspecified | Marked as deferred to Phase 2+ in Section 12 |
| CC-N6: In-memory registry not flagged | Added as known limitation in Section 12 deferrals |
