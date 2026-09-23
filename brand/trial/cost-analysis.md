# call-use Free Trial: Cost Analysis

> Last updated: 2026-03-14

## Per-Minute Cost Breakdown

All prices reflect current (Q1 2026) pay-as-you-go rates for US domestic calls.

| Component | Service | Pricing Model | Est. cost/min |
|-----------|---------|---------------|---------------|
| Telephony | Twilio Elastic SIP Trunking | Per-minute outbound PSTN | $0.014 |
| STT | Deepgram Nova-3 (streaming) | Per-minute audio | $0.0077 |
| LLM | OpenAI GPT-4o | Per token (input + output) | $0.0045 |
| TTS | OpenAI gpt-4o-mini-tts | Per token (text in, audio out) | $0.015 |
| Infrastructure | LiveKit Cloud (Ship plan) | Connection + agent minutes | $0.011 |
| Hosting | Trial gateway (VPS) | Fixed cost amortized | $0.001 |
| **Total** | | | **$0.0532/min** |

### Pricing Assumptions & Sources

**Telephony (Twilio):** US outbound PSTN via Elastic SIP Trunking at $0.014/min. No per-channel or port fees. Source: [Twilio SIP Trunking Pricing](https://www.twilio.com/en-us/sip-trunking/pricing/us).

**STT (Deepgram):** Nova-3 streaming at $0.0077/min (pay-as-you-go). Growth plan drops to $0.0065/min. Source: [Deepgram Pricing](https://deepgram.com/pricing).

**LLM (OpenAI GPT-4o):** $2.50/1M input tokens, $10.00/1M output tokens. Conversational voice estimate: ~150 words/min spoken by user = ~200 input tokens/min. Agent generates ~100 words/min = ~133 output tokens/min. Per-minute cost: (200 * $2.50 / 1M) + (133 * $10.00 / 1M) = $0.0005 + $0.00133 = ~$0.002. Adding system prompt amortization + context window overhead: ~$0.0045/min. Source: [OpenAI Pricing](https://openai.com/api/pricing/).

**TTS (OpenAI gpt-4o-mini-tts):** $0.60/1M text input tokens + $12/1M audio output tokens. ~75 words/min agent speech = ~100 text tokens in, ~1,200 audio tokens out. Per-minute: (100 * $0.60 / 1M) + (1200 * $12 / 1M) = ~$0.015/min. Source: [OpenAI Pricing](https://openai.com/api/pricing/).

**LiveKit Cloud:** Ship plan at $99/mo includes 5,000 agent minutes. Overage: $0.01/agent-min + $0.0005/connection-min. Blended rate ~$0.011/min per session. Source: [LiveKit Pricing](https://livekit.com/pricing).

**Hosting:** Trial gateway on a $20/mo VPS (2 vCPU, 4GB RAM) amortized across ~20,000 minutes/month = $0.001/min. Redis on the same instance.

---

## Per-User Cost (30-Minute Trial)

| Scenario | Minutes Used | Cost per User |
|----------|-------------|---------------|
| **Average case** | 15 min (50% utilization) | $0.80 |
| **Heavy user** | 25 min | $1.33 |
| **Worst case** | 30 min (full budget) | $1.60 |

Most trial users will make 2-3 short test calls (3-5 min each), averaging ~15 minutes total.

---

## Scale Projections

Assumes 15 min average usage per user (50% of 30-min allocation).

| Users/month | Avg minutes used | Monthly cost | Annual cost |
|-------------|-----------------|--------------|-------------|
| 100 | 1,500 | $80 | $958 |
| 500 | 7,500 | $399 | $4,788 |
| 1,000 | 15,000 | $798 | $9,576 |
| 5,000 | 75,000 | $3,990 | $47,880 |
| 10,000 | 150,000 | $7,980 | $95,760 |

### Fixed Costs (included above as amortized, but listed separately)

| Item | Monthly cost | Notes |
|------|-------------|-------|
| LiveKit Cloud (Ship) | $99 | Includes 5,000 agent-min |
| Twilio phone number | $2 | Shared outbound number |
| VPS (gateway + Redis) | $20 | 2 vCPU / 4GB |
| Domain + CDN | $0 | Already on call-use.com |
| **Fixed total** | **$121/mo** | Break-even at ~2,275 min |

---

## Cost Optimization Strategies

### Volume Discounts (achievable at scale)

| Component | Pay-as-you-go | Volume rate | Savings |
|-----------|--------------|-------------|---------|
| Deepgram | $0.0077/min | $0.0065/min (Growth) | 16% |
| Twilio | $0.014/min | $0.012/min (committed use) | 14% |
| LiveKit | $0.011/min | $0.008/min (Scale plan) | 27% |
| OpenAI | Standard | Batch API where possible | 50% on batch |

At 75,000 min/month (5,000 users), switching to volume plans saves ~$600/mo (15%).

### Technical Optimizations

1. **Shorter default trial**: 15 min instead of 30 reduces worst-case cost by 50%.
2. **3-min call cap** for first call (instead of 5 min) -- enough to demo, limits abuse.
3. **Caching system prompts**: Reduce LLM context costs by caching common preambles.
4. **Geographic restriction**: US/Canada only eliminates international telephony surcharges.
5. **Off-peak routing**: No real savings for PSTN, but LLM batch endpoints are 50% cheaper (not applicable for real-time).

### Abuse Prevention (cost-saving impact)

| Measure | Est. cost savings |
|---------|------------------|
| Rate limiting (3 calls/hour/IP) | Prevents bot-driven abuse |
| Phone number dedup | Prevents spam to premium numbers |
| Block premium-rate numbers | Prevents $5+/min call fraud |
| CAPTCHA before first call | Reduces automated abuse by ~90% |
| Browser fingerprint + IP tracking | Prevents trial reset by clearing cookies |

### Cost Comparison: Build vs. Buy

If a user were to set up call-use themselves from scratch:

| Item | DIY cost (monthly) | Notes |
|------|-------------------|-------|
| LiveKit Cloud (Build plan) | $0 (free tier) | 1,000 agent-min included |
| Twilio account + number | $2 + usage | Need own account |
| Deepgram API | $0 (free credits) | $200 free credit |
| OpenAI API | Usage-based | Need own account |
| Setup time | 1-3 hours | Following call-use docs |
| **Effective cost** | **$0 for first ~1,000 min** | Then usage-based |

The free trial's value proposition is **zero setup time** -- try it in 30 seconds instead of 1-3 hours.

---

## Sources

- [Twilio SIP Trunking Pricing](https://www.twilio.com/en-us/sip-trunking/pricing/us)
- [Deepgram Pricing](https://deepgram.com/pricing)
- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [LiveKit Cloud Pricing](https://livekit.com/pricing)
- [Retell AI Pricing Comparison](https://www.retellai.com/resources/voice-ai-platform-pricing-comparison-2025)
- [Voice Agent Pricing Guide](https://p0stman.com/pricing/ai-voice-agent-pricing-guide-2025)
