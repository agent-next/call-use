# call-use Pricing Tiers

> Last updated: 2026-03-14

## Pricing Philosophy

call-use is **open-source** software. Users can always self-host for free -- they only pay their own API providers directly. The paid tiers are for users who want a **managed experience**: no infrastructure setup, shared credentials, usage-based billing, and support.

This is the "open core + managed cloud" model used by PostHog, Supabase, GitLab, and others.

---

## Tier Overview

| Tier | Price | Minutes/month | Per-call limit | Features |
|------|-------|---------------|----------------|----------|
| **Free Trial** | $0 | 30 min (one-time) | 5 min/call | Basic call, real-time transcript |
| **Hobby** | $19/mo | 100 min | 10 min/call | All Free Trial features + call history, webhook delivery |
| **Pro** | $79/mo | 500 min | 30 min/call | All Hobby features + custom voices, priority queue, API access |
| **Scale** | $249/mo | 2,000 min | 60 min/call | All Pro features + dedicated SIP trunk, SLA, bulk calling |
| **Enterprise** | Custom | Unlimited | Unlimited | All Scale features + SSO, audit logs, custom LLM, on-prem option |

### Overage Pricing

| Tier | Overage rate | Notes |
|------|-------------|-------|
| Free Trial | N/A (hard cap) | Must upgrade |
| Hobby | $0.15/min | Capped at $50/mo overage |
| Pro | $0.12/min | Capped at $200/mo overage |
| Scale | $0.08/min | No cap |
| Enterprise | Negotiated | Volume pricing |

---

## Detailed Feature Matrix

| Feature | Free Trial | Hobby | Pro | Scale | Enterprise |
|---------|-----------|-------|-----|-------|------------|
| Outbound calls (US/CA) | Yes | Yes | Yes | Yes | Yes |
| International calling | No | No | Yes (20 countries) | Yes (50+ countries) | Global |
| Real-time transcript | Yes | Yes | Yes | Yes | Yes |
| CallOutcome structured data | Yes | Yes | Yes | Yes | Yes |
| Call history / dashboard | No | 30 days | 90 days | 1 year | Unlimited |
| Webhook delivery | No | Yes | Yes | Yes | Yes |
| REST API access | No | Limited (10 req/min) | Full (100 req/min) | Full (1000 req/min) | Unlimited |
| Custom system prompt | Yes | Yes | Yes | Yes | Yes |
| Custom voices | No | No | Yes (OpenAI voices) | Yes + cloned | Yes + any provider |
| Bulk/batch calling | No | No | No | Yes (10 concurrent) | Yes (100+ concurrent) |
| Dedicated phone number | No | No | Yes | Yes | Yes |
| Dedicated SIP trunk | No | No | No | Yes | Yes |
| LLM model selection | GPT-4o only | GPT-4o only | GPT-4o / Claude | Any supported | Any + custom |
| STT model selection | Deepgram Nova-3 | Deepgram Nova-3 | Deepgram / Whisper | Any supported | Any + custom |
| Call recording | No | No | Yes (opt-in) | Yes | Yes |
| Priority queue | No | No | Yes | Yes | Yes |
| SLA | None | None | None | 99.5% uptime | 99.9% uptime |
| Support | Community | Email (48h) | Email (24h) | Slack (4h) | Dedicated + Slack (1h) |
| SSO / SAML | No | No | No | No | Yes |
| Audit logs | No | No | No | No | Yes |
| On-premise deployment | No | No | No | No | Yes (assisted) |

---

## Unit Economics

### Cost per Minute (at Scale tier, ~2,000 min/mo)

| Component | Cost/min | Notes |
|-----------|----------|-------|
| Twilio SIP | $0.014 | Volume rate |
| Deepgram Nova-3 | $0.0065 | Growth plan |
| OpenAI LLM | $0.0045 | GPT-4o |
| OpenAI TTS | $0.015 | gpt-4o-mini-tts |
| LiveKit Cloud | $0.008 | Scale plan |
| Infrastructure | $0.002 | Amortized |
| **Total COGS** | **$0.050** | |

### Margin Analysis

| Tier | Effective price/min | COGS/min | Gross margin |
|------|-------------------|----------|-------------|
| Hobby ($19/100 min) | $0.19 | $0.053 | 72% |
| Pro ($79/500 min) | $0.158 | $0.051 | 68% |
| Scale ($249/2000 min) | $0.125 | $0.050 | 60% |
| Overage (Hobby) | $0.15 | $0.053 | 65% |
| Overage (Pro) | $0.12 | $0.051 | 58% |
| Overage (Scale) | $0.08 | $0.050 | 38% |

Target gross margin: 55-75% (healthy for infrastructure SaaS).

---

## Competitive Analysis

### Direct Competitors (Voice Agent Platforms)

| Platform | Pricing | All-in cost/min | Model | Notes |
|----------|---------|-----------------|-------|-------|
| **Vapi** | $0.05/min + provider costs | $0.13-0.31/min | Platform fee + pass-through | Orchestration layer; user still pays STT/LLM/TTS separately |
| **Retell AI** | $0.07-0.10/min all-in | $0.07-0.10/min | All-inclusive | Includes STT, simpler setup |
| **Bland AI** | ~$0.09/min | $0.09/min | All-inclusive | Focus on batch calling |
| **ElevenLabs Conv. AI** | $0.08-0.10/min | $0.08-0.10/min | All-inclusive | Best audio quality |
| **call-use (self-hosted)** | $0 (OSS) | ~$0.05/min (own keys) | Self-hosted | Full control, no platform fee |
| **call-use Managed** | $0.08-0.19/min | $0.08-0.19/min | Managed cloud | Zero setup, open-source core |

### Positioning

call-use occupies a unique space: **open-source core with optional managed cloud**.

**vs. Vapi/Retell/Bland:** call-use is cheaper at scale (self-host for $0.05/min with your own keys) and fully transparent (open-source). The managed tier competes on price while offering full portability -- users can always eject to self-hosted.

**vs. DIY (Twilio + LiveKit + own code):** call-use provides the agent framework and call orchestration. You save weeks of development time.

### Value Proposition by Tier

| Tier | Target User | Value Proposition |
|------|------------|-------------------|
| **Free Trial** | Curious developer | "See it work in 30 seconds, no setup" |
| **Hobby** | Side project / indie hacker | "Ship voice features for less than a lunch" |
| **Pro** | Startup / small team | "Production-ready voice agents without DevOps" |
| **Scale** | Growth company | "High-volume calling with SLA and dedicated infra" |
| **Enterprise** | Large org | "Full control, compliance, on-prem option" |

---

## Revenue Projections

Assumes trial -> paid conversion of 5% (industry standard for developer tools).

### Year 1 Projections

| Month | Trial users | Hobby | Pro | Scale | MRR |
|-------|------------|-------|-----|-------|-----|
| 1-3 | 500 | 10 | 3 | 0 | $427 |
| 4-6 | 1,500 | 30 | 10 | 1 | $1,609 |
| 7-9 | 3,000 | 60 | 25 | 3 | $3,862 |
| 10-12 | 5,000 | 100 | 45 | 8 | $7,447 |

**Year 1 total revenue (cumulative): ~$40,000**
**Year 1 trial cost (cumulative): ~$12,000** (15,000 trial users * $0.80 avg)

### Break-Even Analysis

- Fixed costs: ~$200/mo (infrastructure + SaaS subscriptions).
- Trial costs: ~$0.80/user (15 min average).
- Break-even on trial: ~3 paying Hobby users cover 100 trial users.
- Break-even on fixed costs: 11 Hobby users or 3 Pro users.

---

## Migration Path: Trial to Paid

### Upgrade Triggers (shown in UI)

1. **Budget exhausted**: "You've used all 30 free minutes. Upgrade to Hobby for 100 min/mo."
2. **Feature gate**: "Call recording is a Pro feature. Upgrade to unlock."
3. **Call duration**: "Trial calls are limited to 5 min. Upgrade for longer calls."
4. **API access**: "Want to integrate call-use in your app? Upgrade to Hobby for API access."

### Self-Hosted Alternative (always available)

Every upgrade prompt also includes: "Or self-host call-use for free with your own API keys." This builds trust and reduces churn -- users who choose managed are choosing convenience, not lock-in.

---

## Sources

- [Vapi Pricing](https://vapi.ai/pricing)
- [Retell AI Pricing Comparison](https://www.retellai.com/resources/voice-ai-platform-pricing-comparison-2025)
- [Bland AI](https://www.bland.ai/)
- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [Voice Agent Pricing Guide 2026](https://p0stman.com/pricing/ai-voice-agent-pricing-guide-2025)
- [CloudTalk Voice AI Cost Breakdown](https://www.cloudtalk.io/blog/how-much-does-voice-ai-cost/)
