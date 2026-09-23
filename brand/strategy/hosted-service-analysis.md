# call-use Hosted Service Strategy Analysis

> Last updated: 2026-03-14

Should call-use offer a hosted/managed service? This document analyzes the strategic options, recommends an approach, and provides a go-to-market timeline.

---

## 1. Should We Offer a Hosted Service?

**Verdict: Yes, but with a specific model (Option E: Hybrid BYOK Cloud) that minimizes legal exposure while capturing revenue.**

### Arguments FOR

| Argument | Weight | Notes |
|----------|--------|-------|
| Revenue generation | **Critical** | Open source alone does not generate meaningful revenue. curl has 1 employee; nginx sold to F5 for $670M but took 15 years. We need revenue within 12 months. |
| Lower barrier to entry | **High** | The trial architecture shows "zero to first call in 30 seconds" is the killer value prop. Self-hosted requires 1-3 hours of setup. |
| Competitive parity | **High** | Every direct competitor (Bland, Vapi, Retell, Synthflow) is hosted. Developers expect a managed option. |
| Usage data for improvement | **Medium** | Aggregated call patterns, failure modes, and latency data improve the product for everyone. |
| Free trial drives adoption | **High** | The trial architecture (call-use.com/try) already assumes shared infrastructure. A hosted service is the natural upgrade path. |
| Control over quality | **Medium** | Self-hosted users may run suboptimal configs that create bad first impressions. Managed service ensures quality. |

### Arguments AGAINST

| Argument | Weight | Mitigation |
|----------|--------|------------|
| TCPA co-originator liability | **Critical** | BYOK model: user provides their own Twilio credentials. We are infrastructure, not caller. See Section 2, Option D/E. |
| Section 230 does not apply | **High** | Acknowledged. We cannot rely on Section 230 for telephony. Must structure to avoid being the "caller" under TCPA. |
| Infrastructure complexity | **Medium** | Multi-tenant architecture is non-trivial but well-understood. LiveKit Cloud handles the hardest part (media routing). |
| Support burden | **Medium** | Tier support with community -> email -> Slack escalation. Scale with revenue. |
| Abuse potential | **High** | BYOK significantly reduces abuse surface: bad actors need their own Twilio account (which has its own verification). Rate limiting, AUP enforcement, and abuse reporting handle the rest. |
| Regulatory compliance overhead | **Medium** | Compliance tooling (DNC checking, consent management, AI disclosure) becomes a paid feature, not just a cost. |

### The Core Tension

The fundamental tension is:

- **Revenue requires hosting** -- the market expects it, and open-source-only monetization is unreliable.
- **Hosting creates liability** -- the FCC's 2024 ruling and TCPA co-originator doctrine create real legal risk for platforms that originate calls.

The resolution is to **host the infrastructure but not the telephony credentials**. This is the BYOK (Bring Your Own Keys) model.

---

## 2. Business Model Options

### Option A: Pure Open Source (No Hosted Service)

**Model:** MIT-licensed software. Revenue from sponsorships, consulting, and support contracts.

| Dimension | Assessment |
|-----------|------------|
| Revenue (Year 1) | $0-10K (sponsorships, maybe one consulting engagement) |
| Revenue (Year 3) | $20-80K (support contracts if enterprise adopters emerge) |
| Legal risk | **Minimal** -- MIT license + open-source precedent (Asterisk, Metasploit) protects against user misuse |
| Engineering cost | $0 (no hosted infrastructure) |
| Competitive positioning | Unique as "the only open-source option" but no managed alternative loses convenience-seekers to Vapi/Retell |
| Community impact | Best for community trust, worst for sustainability |

**Verdict:** Not viable as a business. Works as a hobby project or loss-leader for a different business. curl took 25 years to get 1 full-time paid contributor. We need revenue faster.

---

### Option B: Open Core

**Model:** MIT core + proprietary paid features (analytics dashboard, call recording storage, compliance tools, multi-worker orchestration).

| Dimension | Assessment |
|-----------|------------|
| Revenue (Year 1) | $10-30K (license sales are slow for early-stage projects) |
| Revenue (Year 3) | $100-400K (if enterprise features land well) |
| Legal risk | **Low-Medium** -- hosting compliance tools implies some co-responsibility for compliance outcomes |
| Engineering cost | **Medium** -- must build proprietary features, maintain two codebases |
| Competitive positioning | Risk of community backlash ("bait and switch"). GitLab and Sentry succeeded but had years of community goodwill first. |
| Community impact | **Negative if done wrong.** Moving useful features behind paywall before community trust is established will kill adoption. call-use has 0 GitHub stars today -- too early for open core. |

**Verdict:** Premature. Open core works when you have massive community adoption and enterprise demand. call-use needs to build community first. Revisit at 5,000+ GitHub stars.

---

### Option C: Hosted Platform (Full SaaS)

**Model:** Fully managed service at call-use.com. Per-minute pricing. call-use operates all infrastructure including Twilio accounts.

| Dimension | Assessment |
|-----------|------------|
| Revenue (Year 1) | $40K (per existing pricing-tiers.md projections) |
| Revenue (Year 3) | $300-800K (if growth continues at projected rates) |
| Legal risk | **HIGH** -- call-use becomes co-originator under TCPA. Shared Twilio account = shared liability. FCC 2024 ruling explicitly covers this. Class action exposure: $500-1,500 per call x thousands of calls = existential risk. |
| Engineering cost | **High** -- multi-tenant infra, billing, abuse detection, compliance tooling, support |
| Competitive positioning | Direct competition with Vapi ($0.30/min), Retell ($0.14/min), Bland ($0.09/min). call-use at $0.08-0.19/min is price-competitive. |
| Community impact | Neutral -- as long as self-hosted remains free and fully functional. |

**Verdict:** Revenue is attractive but legal risk is existential. Operating a shared Twilio account makes call-use a co-originator. One bad actor + one class action = potential bankruptcy. Bland and Vapi accept this risk because they have $25-65M in VC funding and legal teams. call-use does not.

**The shared-Twilio-account model is the single biggest liability in this entire analysis.** It should only be used for the free trial (limited scope, rate-limited, small exposure) and never for paid production traffic.

---

### Option D: BYOK Marketplace

**Model:** Users provide their own Twilio/LiveKit/OpenAI API keys. call-use hosts only the orchestration infrastructure (agent runtime, WebSocket relay, job queue). Per-minute or subscription pricing for infrastructure usage.

| Dimension | Assessment |
|-----------|------------|
| Revenue (Year 1) | $20-40K (lower ARPU than full SaaS, but lower churn due to key ownership) |
| Revenue (Year 3) | $150-500K |
| Legal risk | **Low-Medium** -- user is the caller (their Twilio account, their phone numbers). call-use is a tool/infrastructure provider, analogous to Vercel hosting a Next.js app that sends emails via the user's SendGrid. |
| Engineering cost | **Medium** -- must build secure key management, per-user credential storage, multi-tenant runtime isolation |
| Competitive positioning | Unique: no competitor offers BYOK. Developers who want control but not self-hosting ops have no current option. |
| Community impact | **Positive** -- aligns with open-source values (no vendor lock-in, user controls their data and credentials) |

**Key legal advantage:** When the user provides their own Twilio credentials:
1. The user is the account holder with Twilio (the caller under TCPA)
2. call-use never touches the telephony billing relationship
3. call-use is a software tool, not a telecom service
4. Analogous to how Vercel is not liable for content hosted on its platform, or how Supabase is not liable for data stored in user-owned Postgres instances

**Verdict:** Strong option. Significantly reduces legal risk while enabling revenue. But pure BYOK has a higher friction onboarding (user must set up 4 API accounts before first call).

---

### Option E: Hybrid (Open Source + BYOK Cloud + Premium Features)

**Model:** Combines the best elements:

| Layer | Model | Keys | Pricing |
|-------|-------|------|---------|
| **Self-hosted** | MIT, free forever | User's own | $0 |
| **Free trial** | Shared infrastructure | call-use's (shared Twilio) | $0 (30 min cap) |
| **Cloud (BYOK)** | Managed runtime | User's own (Twilio, LLM, STT, TTS) | $19-249/mo subscription for infrastructure |
| **Cloud features** | Premium add-ons | N/A | Included in tiers or a la carte |

Premium cloud features (not in open-source):
- Analytics dashboard (call duration, success rate, cost tracking)
- Call recording storage and search
- Compliance toolkit (DNC checking, consent management, AI disclosure enforcement)
- Multi-worker orchestration (parallel calls)
- Monitoring and alerting (latency, error rates, budget alerts)
- Webhook management UI
- Team collaboration (shared agents, RBAC)
- Dedicated support (SLA-backed)

| Dimension | Assessment |
|-----------|------------|
| Revenue (Year 1) | $30-60K |
| Revenue (Year 3) | $200-700K |
| Legal risk | **Low** for cloud (BYOK). **Low-Medium** for free trial (shared Twilio, but rate-limited and capped). |
| Engineering cost | **Medium-High** -- must build multi-tenant runtime, key management, premium features, billing |
| Competitive positioning | **Unique and defensible.** "The only open-source voice agent runtime with a managed cloud option. Bring your own keys -- no vendor lock-in, no per-minute tax." |
| Community impact | **Positive** -- self-hosted is free forever. Cloud is optional convenience. Premium features are genuinely new value, not paywalled core features. |

**Verdict: This is the recommended approach.** It threads the needle between revenue generation and legal risk management.

---

## 3. Recommendation: Option E (Hybrid BYOK Cloud)

### Why Option E Wins

**Against Option A (Pure OSS):** Option E generates revenue. Option A does not.

**Against Option B (Open Core):** Option E does not paywall core functionality. The open-source version is complete and fully functional. Premium features are genuinely additive (analytics, compliance tools, multi-worker). Open core risks community backlash; Option E avoids it by keeping the MIT core whole.

**Against Option C (Full SaaS):** Option E avoids co-originator liability by using BYOK. Full SaaS with shared Twilio accounts is an existential legal risk without VC funding and a legal team. The only shared-Twilio exposure is the free trial, which is rate-limited, capped at 30 minutes per user, and low-volume.

**Against Option D (Pure BYOK):** Option E includes premium features that justify the subscription beyond just "we host your runtime." Pure BYOK commoditizes quickly -- the premium features create defensible value.

### Detailed Architecture

```
                    +-----------------------+
                    |    call-use.com       |
                    |  - Landing page       |
                    |  - /try (free trial)  |
                    |  - /cloud (dashboard) |
                    +-----------+-----------+
                                |
                    +-----------+-----------+
                    |   Cloud Control Plane |
                    |  - Auth (Clerk/Auth0) |
                    |  - Billing (Stripe)   |
                    |  - Key vault          |
                    |  - Team management    |
                    +-----------+-----------+
                                |
               +----------------+----------------+
               |                                 |
    +----------+----------+          +-----------+-----------+
    |   Free Trial Pool   |          |   BYOK Worker Pool    |
    |  (shared credentials)|         |  (user credentials)   |
    |  - Rate limited      |         |  - Isolated per user  |
    |  - 30 min cap        |         |  - User's Twilio SIP  |
    |  - 5 min/call        |         |  - User's LLM/STT/TTS |
    +---------------------+          |  - No call limits     |
                                     +-----------------------+
                                                |
                                     +-----------------------+
                                     |   Premium Services    |
                                     |  - Analytics engine   |
                                     |  - Recording storage  |
                                     |  - DNC checker        |
                                     |  - Monitoring/alerts  |
                                     |  - Webhook manager    |
                                     +-----------------------+
```

### Revenue Model

| Tier | Price | What You Get | BYOK? |
|------|-------|-------------|-------|
| **Free Trial** | $0 | 30 min, shared infra, basic features | No (shared) |
| **Starter** | $19/mo | Managed runtime, dashboard, 5 agents, webhook delivery | Yes |
| **Pro** | $79/mo | Everything in Starter + analytics, recording storage, priority support, 20 agents | Yes |
| **Scale** | $249/mo | Everything in Pro + compliance toolkit, multi-worker, monitoring, SLA, unlimited agents | Yes |
| **Enterprise** | Custom | Everything in Scale + SSO, audit logs, dedicated infra, on-prem option | Yes or managed |

Key difference from the existing pricing-tiers.md: **no per-minute pricing from call-use**. Users pay their providers directly for per-minute costs (~$0.05/min). call-use charges a flat subscription for infrastructure and features. This:

1. Eliminates per-minute TCPA liability (we are not billing for calls)
2. Simplifies billing (predictable monthly cost)
3. Aligns incentives (we want users to make more calls, not fewer)
4. Differentiates from every competitor (all charge per-minute)

### Revised Revenue Projections

| Period | Trial Users | Starter | Pro | Scale | MRR | Notes |
|--------|------------|---------|-----|-------|-----|-------|
| Month 1-3 | 500 | 8 | 2 | 0 | $310 | Early adopters |
| Month 4-6 | 1,500 | 25 | 8 | 1 | $1,356 | Content marketing + MCP ecosystem |
| Month 7-9 | 3,000 | 50 | 20 | 3 | $3,297 | SEO + word-of-mouth |
| Month 10-12 | 5,000 | 80 | 35 | 6 | $5,789 | Approaching product-market fit |

**Year 1 cumulative revenue: ~$32,000**
**Year 1 trial cost: ~$8,000** (10,000 trial users x $0.80 avg)
**Year 1 infrastructure cost: ~$6,000** ($500/mo avg)
**Year 1 net: ~$18,000** (not yet sustainable, but validates the model)

**Year 3 projections (if growth continues):**

| Metric | Conservative | Moderate | Optimistic |
|--------|-------------|----------|------------|
| Paying customers | 300 | 600 | 1,200 |
| MRR | $18K | $42K | $95K |
| ARR | $216K | $504K | $1.14M |
| Gross margin | 70% | 75% | 80% |

### Competitive Positioning

```
"call-use Cloud: The only open-source voice agent runtime with a managed option.

- Self-host free, forever (MIT license)
- Cloud: bring your own API keys -- no per-minute platform tax
- You control your Twilio account, your LLM, your data
- We handle the infrastructure, monitoring, and premium features
- Switch between self-hosted and cloud anytime -- zero lock-in"
```

This is a positioning that **no competitor can match**:
- Bland/Vapi/Retell cannot offer self-hosting or BYOK
- Vocode/LiveKit cannot offer a managed agent runtime with premium features
- Nobody offers the combination of open-source + managed + BYOK

---

## 4. Go-To-Market Timeline

### Phase 1: Foundation (Month 1-3)

**Goal:** Launch free trial + validate demand.

| Week | Deliverable | Owner |
|------|------------|-------|
| 1-2 | Trial gateway API (FastAPI) -- per trial-architecture.md | Engineering |
| 3-4 | Frontend widget (call-use.com/try) | Engineering |
| 5-6 | Anti-abuse measures (rate limiting, Turnstile, number validation) | Engineering |
| 7-8 | Legal: finalize ToS + AUP (per tos-outline.md) | Legal counsel |
| 9-10 | Compliance disclaimers in product + docs | Engineering + Legal |
| 11-12 | Launch free trial publicly | All |

**KPIs:**
- 500+ trial users in first 3 months
- < $0.90 average cost per trial user
- < 1% abuse rate
- NPS > 40 from trial users

**Legal checklist (must complete before trial launch):**
- [ ] ToS published and checkbox-gated
- [ ] AUP published
- [ ] Abuse reporting process live (abuse@call-use.com)
- [ ] AI disclosure enforced in default system prompt
- [ ] Rate limiting and kill switch operational
- [ ] Business insurance (general liability + E&O) obtained

### Phase 2: Cloud Beta (Month 4-6)

**Goal:** Launch BYOK cloud for paying customers.

| Week | Deliverable | Owner |
|------|------------|-------|
| 1-3 | Auth system (Clerk or Auth0) | Engineering |
| 3-5 | Secure key vault for user API credentials | Engineering |
| 5-7 | Multi-tenant worker orchestration (isolated per-user runtimes) | Engineering |
| 7-9 | Billing integration (Stripe subscriptions) | Engineering |
| 9-10 | Basic dashboard (call history, usage stats) | Engineering |
| 10-11 | Beta launch to trial users who expressed interest | Product |
| 11-12 | Iterate based on beta feedback | All |

**KPIs:**
- 20+ beta users onboarded
- < 2 hour setup time from signup to first BYOK call
- 95%+ uptime during beta
- 3+ paying conversions from beta

**Technical requirements:**
- [ ] Per-user credential isolation (no cross-tenant key access)
- [ ] Worker isolation (containerized or process-level)
- [ ] Graceful degradation when user keys are invalid/expired
- [ ] Usage metering (for future analytics features)
- [ ] Audit logging (who did what, when)

### Phase 3: General Availability (Month 7-12)

**Goal:** Full cloud launch with premium features.

| Month | Deliverable |
|-------|------------|
| 7 | GA launch: Starter + Pro tiers live |
| 8 | Analytics dashboard (call duration, success rates, cost tracking) |
| 9 | Call recording storage + search |
| 10 | Compliance toolkit (DNC checker, consent management) |
| 11 | Multi-worker orchestration (parallel calls for Scale tier) |
| 12 | Scale tier launch + monitoring/alerting |

**KPIs:**
- 80+ paying customers by month 12
- MRR > $4,000 by month 12
- Churn < 8% monthly
- Trial-to-paid conversion > 3%

---

## 5. Key Decision Points

### What Must Be True Before Launching the Free Trial

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Legal** | | |
| ToS drafted and reviewed by telecom attorney | Not started | Budget ~$3-5K for attorney review |
| AUP published | Not started | Template exists in tos-outline.md |
| Business entity formed (LLC minimum) | Unknown | Required for liability protection |
| General liability + E&O insurance | Not started | Budget ~$1-3K/year |
| Abuse reporting process operational | Not started | abuse@call-use.com + web form |
| **Technical** | | |
| Trial gateway API deployed | Not started | Per trial-architecture.md |
| Rate limiting + kill switch | Not started | Redis-backed |
| Anti-abuse (Turnstile, number validation) | Not started | |
| Default AI disclosure in system prompt | Not started | FCC requirement |
| Shared API key spending caps | Not started | $500/mo OpenAI hard cap |
| **Financial** | | |
| $500/mo runway for trial infrastructure | Required | LiveKit $99 + VPS $20 + API usage |
| Payment processing setup (Stripe) | Not needed for trial | Needed for Phase 2 |
| **Team** | | |
| On-call rotation for trial monitoring | Required | Even if it is 1 person |
| Abuse response process (< 24h SLA) | Required | |

### What Must Be True Before Launching BYOK Cloud

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Legal** | | |
| Updated ToS covering paid service | Not started | Expand trial ToS |
| DPA (Data Processing Agreement) template | Not started | Required for enterprise |
| Subprocessor list published | Not started | Twilio, LiveKit, cloud provider |
| **Technical** | | |
| Secure credential vault | Not started | AWS Secrets Manager, Vault, or encrypted DB |
| Multi-tenant worker isolation | Not started | Containers or process-level isolation |
| Auth + billing integration | Not started | Clerk/Auth0 + Stripe |
| Automated provisioning (signup -> first call) | Not started | Target: < 10 min |
| Health monitoring + alerting | Not started | PagerDuty or similar |
| **Financial** | | |
| $2K/mo runway for cloud infrastructure | Required | Scales with users |
| Stripe account verified for subscriptions | Required | |
| **Team** | | |
| Support process (email SLA) | Required | 48h for Starter, 24h for Pro |
| On-call escalation path | Required | |

### Key Risk Decisions

**Decision 1: Should the free trial use shared Twilio credentials?**

*Recommendation: Yes, but with strict limits.*

The trial is the primary conversion funnel. Requiring users to set up their own Twilio account before trying call-use would kill conversion. The shared Twilio account is acceptable because:
- 30-minute lifetime cap per user
- 5-minute per-call cap
- Rate limiting (5 calls/hour/IP)
- CAPTCHA gate
- Kill switch available
- Total monthly exposure: ~$800-8,000 depending on trial volume (manageable)

The legal exposure from the trial is bounded and manageable. The paid cloud service (BYOK) eliminates this risk entirely.

**Decision 2: Should we charge per-minute or flat subscription?**

*Recommendation: Flat subscription.*

Per-minute pricing:
- Creates TCPA co-originator risk (we profit per call, we are incentivized to maximize calls)
- Requires metering infrastructure
- Creates bill shock for users
- Competes head-to-head with well-funded competitors on price

Flat subscription:
- No per-call profit = stronger legal position
- Predictable revenue
- Simpler billing
- Differentiated positioning ("no per-minute platform tax")
- Users pay their providers directly for usage

**Decision 3: When to hire a telecom attorney?**

*Recommendation: Before trial launch (Phase 1, Week 7-8).*

Budget $3-5K for initial ToS + AUP review. This is non-negotiable. The risk matrix shows TCPA class actions and FCC enforcement as Critical-impact risks. A $3K attorney review is insurance against $500K+ exposure.

**Decision 4: When to incorporate?**

*Recommendation: Before trial launch.*

Operating a service that makes phone calls without a business entity exposes personal assets. An LLC costs $100-500 to form and provides essential liability protection. Do this before any user makes a call through shared infrastructure.

---

## 6. Summary

| Question | Answer |
|----------|--------|
| Should call-use offer a hosted service? | **Yes** |
| Which model? | **Option E: Hybrid (OSS + Free Trial + BYOK Cloud + Premium Features)** |
| Why not full SaaS? | TCPA co-originator liability is existential without VC funding and legal team |
| Why BYOK? | User provides their own Twilio credentials = user is the caller, not call-use |
| What about the free trial? | Shared credentials are acceptable with strict limits (30 min cap, rate limiting) |
| Pricing model? | Flat subscription ($19-249/mo), NOT per-minute |
| Year 1 revenue? | ~$32K (conservative) |
| Year 3 ARR? | $200K-1.1M (range depends on growth) |
| Biggest risk? | Legal -- must have ToS, AUP, LLC, and insurance before launch |
| Biggest opportunity? | Unique positioning: only open-source + managed + BYOK voice agent runtime |
| Timeline to first revenue? | Month 4-6 (cloud beta) |

---

## Sources

- call-use existing analysis: trial/cost-analysis.md, trial/pricing-tiers.md, trial/trial-architecture.md
- call-use legal analysis: legal/platform-liability.md, legal/risk-matrix.md, legal/regulatory-landscape.md, legal/tos-outline.md
- call-use competitive analysis: competitor-analysis.md
- [Supabase BYOK model](https://supabase.com/docs/guides/platform/bring-your-own-cloud)
- [Grafana Cloud pricing](https://grafana.com/pricing/)
- [Vercel pricing model](https://vercel.com/pricing)
- [PostHog open-source + cloud model](https://posthog.com/pricing)
- [FCC Declaratory Ruling on AI Voices (Feb 2024)](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal)
- [TCPA co-originator doctrine](https://www.henson-legal.com/ai-voice-compliance)
