# call-use Free Trial: Architecture Design

> Last updated: 2026-03-14

## User Flow

```
1. User visits call-use.com/try
2. Sees a simple form:
   - Phone number to call (US/Canada only)
   - Agent instructions (text area, e.g., "Call and ask about their business hours")
   - Optional: agent voice selection
3. Solves a lightweight CAPTCHA (Cloudflare Turnstile -- invisible for most users)
4. Clicks "Make Call"
5. System validates phone number, checks budget, creates trial session
6. Agent dials out via shared infrastructure
7. User sees real-time transcript streaming on the page
8. Call ends (max 5 min/call) -- user sees CallOutcome + full transcript
9. User can make more calls until 30-min budget is exhausted
10. After budget exhaustion: "Loved it? Set up call-use in 5 minutes" CTA
```

### Key UX Principles

- **Zero registration**: No email, no account, no OAuth. Just a phone number and instructions.
- **Instant gratification**: Call starts within 5 seconds of clicking "Make Call."
- **Transparency**: Show real-time transcript so user can see the agent working.
- **Clear limits**: Display remaining minutes prominently.
- **Smooth upgrade path**: After trial, guide to self-hosted setup with clear docs.

---

## User Identification (No Registration)

### Recommended: Option A -- Browser Fingerprint + IP (Hybrid)

| Approach | Friction | Abuse Resistance | Privacy | Recommendation |
|----------|----------|-----------------|---------|----------------|
| **A: Browser fingerprint + IP** | None | Medium | Good (no PII stored) | **Recommended for v0.1** |
| B: Email-only | Low | Medium-High | Moderate (stores email) | Good for v0.2 |
| C: GitHub OAuth | Low | High | Good (OAuth token only) | Best for developer audience |

**Why Option A for v0.1:**
- Zero friction maximizes trial conversion.
- Developer audience is less likely to abuse than consumer audience.
- Fingerprint libraries (e.g., FingerprintJS open-source) generate a stable ID from browser properties.
- Combined with IP, it provides reasonable uniqueness without storing PII.
- If abuse becomes a problem, upgrade to Option B or C later.

**Implementation:**
- Generate a `trial_id` = SHA-256(fingerprint + IP subnet /24).
- Store `trial_id -> { minutes_used, calls_made, created_at }` in Redis with 90-day TTL.
- No PII is stored -- only the hashed identifier and usage counters.

---

## Anti-Abuse Measures

### Layer 1: Input Validation (Immediate)

| Check | Rule | Action |
|-------|------|--------|
| Phone format | E.164, US/CA only (+1...) | Reject with error |
| Premium-rate numbers | Block 1-900, 1-976, shortcodes | Reject with error |
| Toll-free numbers | Block 1-800/888/877/866/855/844 | Reject with error |
| Number length | Exactly 11 digits (1 + 10) | Reject with error |

### Layer 2: Rate Limiting (Per-Session)

| Limit | Value | Window |
|-------|-------|--------|
| Calls per IP | 5 | Per hour |
| Calls per trial_id | 10 | Lifetime |
| Calls to same number | 3 | Per hour |
| Concurrent calls per trial_id | 1 | Real-time |
| Max call duration | 5 min | Per call |
| Total trial budget | 30 min | Lifetime |

### Layer 3: Pre-Call Gates

1. **Cloudflare Turnstile** (invisible CAPTCHA): Runs before first call. Blocks automated scripts with zero friction for real users.
2. **Instruction content filter**: Basic check for prompt injection or malicious instructions (e.g., "ignore your instructions and...").
3. **Phone number reputation** (optional, v0.2): Use Twilio Lookup API to check number type (mobile/landline/VoIP) and carrier.

### Layer 4: Real-Time Monitoring

- **Cost alert**: Notify ops if hourly spend exceeds $50 (abnormal for trial traffic).
- **Kill switch**: Redis flag `trial:enabled` -- set to `false` to instantly halt all trial calls.
- **Per-IP anomaly detection**: Flag IPs that cycle through many fingerprints (proxy/VPN abuse).

---

## Infrastructure Architecture

```
                    call-use.com/try (Static frontend)
                            |
                            v
                  +-----------------------+
                  |  Trial Gateway API    |  (FastAPI on VPS)
                  |  - Validate input     |
                  |  - Check budget       |
                  |  - Rate limit         |
                  |  - Create call-use    |
                  |    session            |
                  +-----------+-----------+
                              |
                   +----------+----------+
                   |                     |
                   v                     v
            +------------+      +------------------+
            |   Redis    |      |  call-use worker |
            | - Budgets  |      |  (existing code) |
            | - Rate     |      |  - LiveKit agent |
            |   limits   |      |  - STT/LLM/TTS  |
            | - Sessions |      +--------+---------+
            +------------+               |
                                         v
                              +--------------------+
                              | Shared LiveKit     |
                              | Cloud Instance     |
                              +--------+-----------+
                                       |
                                       v
                              +--------------------+
                              | Shared Twilio SIP  |
                              | Trunk              |
                              +--------+-----------+
                                       |
                                       v
                                  PSTN Call
```

### Component Details

#### Trial Gateway API (new service)

- **Runtime**: FastAPI (Python 3.12) -- same ecosystem as call-use.
- **Hosting**: Single VPS (2 vCPU, 4GB RAM, $20/mo) or Fly.io ($5-10/mo).
- **Responsibilities**:
  - Accept trial call requests from frontend.
  - Validate phone number, check rate limits, check budget.
  - Spawn a call-use session with shared credentials.
  - Stream transcript events back to frontend via WebSocket.
  - Record call outcome and update budget in Redis.

#### Redis (session store)

- **Data model**:
  ```
  trial:{trial_id}:budget     -> { total_seconds: 1800, used_seconds: 0 }
  trial:{trial_id}:calls      -> [ { call_id, phone, duration, timestamp } ]
  trial:rate:{ip}:hourly       -> counter (TTL: 1 hour)
  trial:rate:{phone}:hourly    -> counter (TTL: 1 hour)
  trial:enabled                -> "true" | "false"  (kill switch)
  ```
- **Hosting**: Same VPS as gateway, or Redis Cloud free tier (30MB, sufficient for ~100K sessions).

#### Shared Credentials

All trial calls use a single set of API keys owned by the call-use project:

| Service | Credential | Notes |
|---------|-----------|-------|
| LiveKit Cloud | API key + secret | Ship plan ($99/mo) |
| Twilio | Account SID + Auth Token | Single SIP trunk |
| Deepgram | API key | Pay-as-you-go |
| OpenAI | API key | Usage-based with spending limit |

**Security**: Keys are stored as environment variables on the gateway VPS, never exposed to the frontend. OpenAI spending limit set to $500/mo as a hard cap.

#### Frontend Widget

- **Stack**: Vanilla HTML/JS or lightweight framework (Preact) -- embedded on call-use.com/try.
- **Features**:
  - Phone number input with country code picker (locked to US/CA).
  - Instructions textarea with character limit (500 chars).
  - "Make Call" button with Turnstile integration.
  - Real-time transcript display (WebSocket from gateway).
  - Call status indicator (dialing, ringing, connected, ended).
  - Remaining budget display.
  - CallOutcome display after call ends.

---

## Data Flow: Making a Trial Call

```
1. Frontend POST /api/trial/call
   Body: { trial_id, phone, instructions, turnstile_token }

2. Gateway validates:
   a. Verify Turnstile token with Cloudflare API
   b. Check trial:enabled flag in Redis
   c. Validate phone number format + block premium numbers
   d. Check rate limits (IP, trial_id, phone)
   e. Check remaining budget >= 60 seconds (minimum call)

3. Gateway creates call-use session:
   a. Generate unique call_id
   b. Configure CallUse with shared credentials
   c. Set max_duration = min(300, remaining_budget_seconds)
   d. Start call-use worker in subprocess

4. Gateway streams events to frontend via WebSocket:
   a. call.started -> show "Connected" status
   b. transcript.update -> append to transcript display
   c. call.ended -> show CallOutcome, update budget display

5. On call end:
   a. Record actual duration in Redis
   b. Deduct from trial budget
   c. Log call metadata (no transcript stored server-side for privacy)
```

---

## Failure Modes & Mitigations

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Redis down | Can't check budgets | Fail closed (reject calls) |
| LiveKit outage | Calls can't connect | Show "Service temporarily unavailable" |
| Twilio outage | PSTN unavailable | Show error, suggest trying later |
| OpenAI rate limit | LLM/TTS fails | Queue with backoff; show "High demand" message |
| Deepgram down | STT fails | Fallback to OpenAI Whisper (higher latency) |
| Cost spike | Budget overrun | Kill switch + $500/mo OpenAI cap + Twilio spend alert |
| DDoS on gateway | Service unavailable | Cloudflare proxy + rate limiting |

---

## Privacy & Compliance

- **No PII stored**: Only hashed trial_id, call metadata (duration, timestamp). No transcripts stored server-side.
- **Phone numbers**: Passed directly to Twilio, not logged. Twilio's own compliance handles TCPA.
- **TCPA considerations**: Trial user is the "caller" -- they initiate the call and provide the number. The call-use agent acts on their behalf. A disclaimer on the form: "By clicking Make Call, you confirm you have consent to call this number."
- **Data retention**: Redis TTL of 90 days on all trial data. No long-term storage.
