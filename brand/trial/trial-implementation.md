# call-use Free Trial: Implementation Plan

> Last updated: 2026-03-14

## Overview

Build a minimal trial system that lets users make AI-powered outbound calls from call-use.com/try with zero registration. The system wraps the existing call-use runtime with a thin gateway layer for budget tracking and rate limiting.

---

## Phase 1: Trial Gateway API (Week 1-2)

### Service: `trial-gateway`

**Tech stack:** FastAPI + Redis + uvicorn

**Directory structure:**
```
call-use-trial/
  gateway/
    main.py              # FastAPI app
    config.py            # Environment variables, limits
    models.py            # Pydantic models
    routes/
      trial.py           # POST /api/trial/call, GET /api/trial/budget
      health.py          # GET /health
    services/
      budget.py          # Redis budget tracking
      rate_limiter.py    # Rate limit checks
      phone_validator.py # E.164 validation, premium number blocking
      turnstile.py       # Cloudflare Turnstile verification
      call_manager.py    # Spawns call-use sessions
    ws/
      transcript.py      # WebSocket handler for real-time transcript
  tests/
    test_budget.py
    test_rate_limiter.py
    test_phone_validator.py
  Dockerfile
  docker-compose.yml     # gateway + redis
  requirements.txt
  Makefile
```

### API Endpoints

```
POST /api/trial/call
  Request:  { trial_id: str, phone: str, instructions: str, turnstile_token: str }
  Response: { call_id: str, ws_url: str }
  Errors:   400 (invalid input), 429 (rate limited), 403 (budget exhausted)

GET  /api/trial/budget?trial_id=xxx
  Response: { total_seconds: 1800, used_seconds: 450, calls_made: 3 }

WS   /ws/trial/{call_id}
  Messages: { type: "status"|"transcript"|"outcome", data: {...} }

GET  /health
  Response: { status: "ok", trial_enabled: true }
```

### Key Implementation Details

**Budget tracking (Redis):**
```python
async def check_and_reserve_budget(trial_id: str, max_seconds: int = 300) -> int:
    """Reserve up to max_seconds from trial budget. Returns reserved seconds."""
    key = f"trial:{trial_id}:budget"
    budget = await redis.hgetall(key)
    if not budget:
        # New user -- initialize budget
        await redis.hset(key, mapping={"total": 1800, "used": 0})
        await redis.expire(key, 90 * 86400)  # 90-day TTL
        remaining = 1800
    else:
        remaining = int(budget["total"]) - int(budget["used"])

    if remaining < 60:
        raise BudgetExhausted()

    reserved = min(max_seconds, remaining)
    return reserved

async def finalize_call(trial_id: str, call_id: str, actual_seconds: int):
    """Deduct actual usage from budget after call ends."""
    await redis.hincrby(f"trial:{trial_id}:budget", "used", actual_seconds)
```

**Phone validation:**
```python
BLOCKED_PREFIXES = ["1900", "1976", "1800", "1888", "1877", "1866", "1855", "1844"]
BLOCKED_PATTERN = re.compile(r"^\+1(900|976|800|888|877|866|855|844)")

def validate_phone(phone: str) -> str:
    """Validate and normalize to E.164. US/CA only."""
    cleaned = re.sub(r"[^\d+]", "", phone)
    if not cleaned.startswith("+1"):
        cleaned = "+1" + cleaned.lstrip("+").lstrip("1")
    if len(cleaned) != 12:  # +1 + 10 digits
        raise InvalidPhone("Must be a valid US or Canadian number")
    if BLOCKED_PATTERN.match(cleaned):
        raise BlockedNumber("Premium-rate and toll-free numbers are not allowed")
    return cleaned
```

**Call manager (wraps call-use):**
```python
async def start_trial_call(call_id: str, phone: str, instructions: str, max_duration: int):
    """Start a call-use session with shared credentials and duration cap."""
    # Import call-use and configure with shared credentials
    from call_use import CallUse

    cu = CallUse(
        phone_number=phone,
        instructions=instructions,
        livekit_url=settings.LIVEKIT_URL,
        livekit_api_key=settings.LIVEKIT_API_KEY,
        livekit_api_secret=settings.LIVEKIT_API_SECRET,
        twilio_account_sid=settings.TWILIO_SID,
        twilio_auth_token=settings.TWILIO_TOKEN,
        sip_trunk_id=settings.TWILIO_SIP_TRUNK_ID,
        deepgram_api_key=settings.DEEPGRAM_KEY,
        openai_api_key=settings.OPENAI_KEY,
        max_call_duration=max_duration,
    )
    outcome = await cu.run()
    return outcome
```

---

## Phase 2: Frontend Widget (Week 2-3)

### Stack: Preact + TypeScript (lightweight, <15KB gzipped)

**Features:**
1. Phone number input with formatting (auto-add +1 prefix).
2. Instructions textarea (500 char limit) with placeholder examples.
3. "Make Call" button with loading state.
4. Cloudflare Turnstile widget (invisible mode).
5. Real-time transcript panel (WebSocket).
6. Call status bar (Dialing -> Ringing -> Connected -> Ended).
7. Budget indicator (remaining minutes).
8. CallOutcome display (structured result from call-use).
9. CTA after trial: "Set up call-use yourself" with link to docs.

**Fingerprint generation:**
```typescript
import FingerprintJS from '@fingerprintjs/fingerprintjs';

async function getTrialId(): Promise<string> {
  const fp = await FingerprintJS.load();
  const result = await fp.get();
  return result.visitorId; // Stable browser fingerprint
}
```

**Hosting:** Static files served from call-use.com/try via existing site hosting (Vercel/Cloudflare Pages).

---

## Phase 3: Monitoring & Alerting (Week 3)

### Cost Monitoring

| Metric | Alert Threshold | Channel |
|--------|----------------|---------|
| Hourly trial spend | > $50 | Slack + email |
| Daily trial spend | > $200 | Slack + email |
| Monthly trial spend | > $2,000 | Slack + email + kill switch |
| Failed call rate | > 20% in 1 hour | Slack |
| Concurrent trial calls | > 10 | Slack (capacity warning) |

### Implementation

**Option A: Lightweight (v0.1)**
- Cron job every 5 min queries Redis for usage counters.
- Calculates estimated spend = minutes * $0.053.
- Sends Slack webhook if threshold exceeded.
- Sets `trial:enabled = false` if monthly cap hit.

**Option B: Full observability (v0.2)**
- Prometheus metrics exported from gateway.
- Grafana dashboard for real-time spend, call volume, error rates.
- PagerDuty integration for critical alerts.

### Kill Switch

```python
# Check on every call request
async def is_trial_enabled() -> bool:
    return await redis.get("trial:enabled") != "false"

# Manual activation
# redis-cli SET trial:enabled false

# Automatic activation (in monitoring cron)
async def check_monthly_cap():
    total_minutes = await get_total_trial_minutes_this_month()
    estimated_cost = total_minutes * 0.053
    if estimated_cost > MONTHLY_CAP:
        await redis.set("trial:enabled", "false")
        await send_alert("Trial kill switch activated: monthly cap exceeded")
```

---

## Phase 4: Hardening (Week 4)

### Security Checklist

- [ ] Rate limiter tested under load (locust/k6).
- [ ] Phone validation covers all premium-rate prefixes.
- [ ] Turnstile integration verified (test with bot traffic).
- [ ] Shared API keys have spending limits set:
  - OpenAI: $500/mo hard cap.
  - Twilio: $200/mo spend trigger.
  - Deepgram: $100/mo alert.
- [ ] Gateway behind Cloudflare proxy (DDoS protection).
- [ ] Redis secured (no public access, AUTH enabled).
- [ ] Environment variables not logged or exposed.
- [ ] Content filter on instructions field (block prompt injection patterns).

### Load Testing Targets

| Metric | Target |
|--------|--------|
| Concurrent trial calls | 10 |
| API response time (P99) | < 200ms |
| WebSocket latency | < 100ms |
| Call setup time | < 5 seconds |

---

## Deployment

### Infrastructure Requirements

| Component | Spec | Monthly Cost |
|-----------|------|-------------|
| VPS (gateway) | 2 vCPU, 4GB RAM (Hetzner/Fly.io) | $10-20 |
| Redis | Same VPS or Redis Cloud (30MB free) | $0 |
| Cloudflare | Free plan (DNS + proxy + Turnstile) | $0 |
| Domain | call-use.com (existing) | $0 |
| **Total fixed** | | **$10-20/mo** |

### Deployment Pipeline

```
1. Docker build (gateway + redis)
2. Push to container registry
3. Deploy to VPS via docker-compose
4. Health check: GET /health
5. Smoke test: Make a test call to a known number
```

### docker-compose.yml (simplified)

```yaml
services:
  gateway:
    build: ./gateway
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - TWILIO_SID=${TWILIO_SID}
      - TWILIO_TOKEN=${TWILIO_TOKEN}
      - TWILIO_SIP_TRUNK_ID=${TWILIO_SIP_TRUNK_ID}
      - DEEPGRAM_KEY=${DEEPGRAM_KEY}
      - OPENAI_KEY=${OPENAI_KEY}
      - TURNSTILE_SECRET=${TURNSTILE_SECRET}
      - MONTHLY_CAP=2000
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

volumes:
  redis-data:
```

---

## Timeline Summary

| Phase | Scope | Duration | Dependencies |
|-------|-------|----------|-------------|
| 1 | Trial Gateway API | Week 1-2 | call-use stable release |
| 2 | Frontend Widget | Week 2-3 | Phase 1 API ready |
| 3 | Monitoring & Alerting | Week 3 | Phase 1 deployed |
| 4 | Hardening & Load Test | Week 4 | Phase 1-3 complete |
| **Total** | **MVP launch** | **4 weeks** | |

### Post-MVP (Month 2+)

- Phone number reputation checks (Twilio Lookup).
- Email verification option (upgrade from fingerprint-only).
- Call recording playback (opt-in, with consent disclosure).
- Analytics dashboard (conversion funnel, popular use cases).
- A/B test trial limits (15 min vs. 30 min).
