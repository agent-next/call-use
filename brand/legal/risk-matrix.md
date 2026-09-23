# call-use Risk Matrix

> Last updated: 2026-03-14

Risk assessment for call-use as an open-source AI calling tool and planned hosted service.

**Disclaimer**: This risk matrix is informational only and does not constitute legal advice.

---

## Risk Scoring

**Likelihood**: Low / Low-Medium / Medium / Medium-High / High
**Impact**: Low / Medium / High / Critical

---

## Risk Matrix

| # | Risk | Likelihood | Impact | Primary Exposure | Mitigation |
|---|------|-----------|--------|-----------------|------------|
| 1 | **User violates TCPA** (calls without consent) | **High** | **Medium** (user liability, not platform for self-hosted) | Users | Compliance guide, prominent disclaimers, in-app consent checklist, ToS requiring compliance |
| 2 | **FCC enforcement against platform** (hosted version) | **Low** | **Critical** (fines, shutdown order) | call-use entity | Disclaimers, AUP, abuse monitoring, rate limiting, no hosted spam tolerance, prompt response to complaints |
| 3 | **State Attorney General action** | **Low-Medium** | **High** (injunction, fines, reputational) | call-use entity + users | Per-state compliance documentation, state-specific calling restrictions, responsive abuse process |
| 4 | **Caller ID spoofing misuse** | **Medium** | **High** (federal fines up to $10K/violation, carrier blacklisting) | Users + platform reputation | Twilio number verification, prohibit arbitrary caller ID, planned ownership verification, AUP prohibition |
| 5 | **Spam/robocall abuse** (mass unsolicited calls) | **Medium** | **High** (reputation damage, Twilio account termination, regulatory attention) | Platform reputation | Rate limiting, per-account call caps, Twilio usage monitoring, AUP enforcement, abuse reporting channel |
| 6 | **Recording consent violation** (two-party consent states) | **Medium** | **Medium** (state criminal charges for users, civil liability $5K+/violation) | Users | Recording disclaimer feature in default prompts, documentation of two-party consent states, configurable recording behavior |
| 7 | **AI voice disclosure failure** (not revealing AI nature) | **Medium** | **Medium** (FCC enforcement, state fines e.g. CA $500/interaction) | Users | Default system prompt includes AI disclosure, documentation requirement, cannot easily disable disclosure in hosted version |
| 8 | **TCPA class action lawsuit** (against hosted service) | **Low-Medium** | **Critical** ($500-$1,500 per call, class can be thousands of calls) | call-use entity | Strong ToS with indemnification, user consent verification, call volume limits on trial, insurance |
| 9 | **Twilio account termination** (abuse by users) | **Medium** | **High** (service interruption for all hosted users) | Platform operations | Separate Twilio sub-accounts per user, proactive monitoring, abuse response SLA, backup carrier relationship |
| 10 | **Patent trolls** (software/method patents) | **Low** | **Medium** (defense costs $100K+, potential licensing) | call-use entity | MIT license, document prior art, monitor patent landscape, consider patent pledge |
| 11 | **Trademark disputes** ("call-use" name) | **Low** | **Low** (rebranding costs if lost) | call-use entity | Register "call-use" trademark, conduct trademark search before launch, monitor for conflicts |
| 12 | **Data breach** (call recordings, transcripts, PII) | **Low-Medium** | **High** (notification obligations, fines under CCPA/state breach laws, reputational) | call-use entity (hosted) | Encryption at rest and in transit, minimal data retention, access controls, breach response plan, security audits |
| 13 | **GDPR/international compliance violation** (if expanding beyond US) | **Low** (currently US-only) | **High** (fines up to 4% global revenue or EUR 20M) | call-use entity | Do not process EU/UK data until compliance framework is built, geo-blocking, data processing agreements |
| 14 | **Vicarious liability for user fraud** (AI phishing, impersonation) | **Low-Medium** | **Critical** (criminal exposure, massive reputational damage) | call-use entity | Content monitoring on hosted version, voice cloning restrictions, identity verification for hosted users, law enforcement cooperation |
| 15 | **FTC enforcement** (TSR violation via hosted service) | **Low** | **High** (fines up to $50,120/violation) | call-use entity | TSR compliance in ToS, DNC scrubbing requirements, telemarketing-specific restrictions |
| 16 | **Carrier blocking** (calls flagged as spam by analytics) | **Medium-High** | **Medium** (reduced call completion rates, degraded service) | Platform operations + users | STIR/SHAKEN compliance via Twilio, reasonable call volumes, caller ID reputation monitoring, number rotation strategy |
| 17 | **Open-source fork used for illegal purposes** | **Medium** | **Low** (reputational only, no legal liability for forks) | Reputation | Cannot prevent, but clear positioning for legitimate use, prominent legal disclaimers in repo |
| 18 | **Employee/contractor liability** (if operating hosted service) | **Low** | **Medium** (personal liability for officers/directors) | Individuals | Proper corporate structure (LLC or Corp), D&O insurance, compliance training |

---

## Priority Actions (by risk severity)

### Immediate (Before Hosted Trial Launch)

1. **Draft and publish Terms of Service + AUP** — mitigates risks #1, #2, #3, #4, #5, #8, #14, #15
2. **Implement rate limiting and abuse monitoring** — mitigates risks #5, #9, #16
3. **Add legal disclaimer to README and docs** — mitigates risks #1, #6, #7, #17
4. **Configure default AI disclosure in system prompts** — mitigates risk #7
5. **Implement recording consent disclaimer as default** — mitigates risk #6
6. **Set up abuse reporting process** — mitigates risks #2, #3, #5, #14

### Short-Term (Within 3 Months of Launch)

7. **Register "call-use" trademark** — mitigates risk #11
8. **Obtain business insurance (general liability + E&O)** — mitigates risks #8, #10, #18
9. **Implement per-user Twilio sub-accounts** — mitigates risk #9
10. **Publish compliance guide for users** — mitigates risks #1, #6, #7
11. **Implement caller ID ownership verification** — mitigates risk #4
12. **Establish data retention and deletion policies** — mitigates risk #12

### Medium-Term (3-6 Months)

13. **Security audit of hosted infrastructure** — mitigates risk #12
14. **Patent landscape review** — mitigates risk #10
15. **International compliance assessment** (if expanding) — mitigates risk #13
16. **D&O insurance for officers** — mitigates risk #18
17. **Carrier reputation monitoring** — mitigates risk #16

---

## Risk Trend Assessment

| Trend | Direction | Rationale |
|-------|-----------|-----------|
| Regulatory scrutiny of AI calling | **Increasing** | FCC 2024 ruling was just the start; NOI on AI in telecom signals more regulation coming |
| TCPA enforcement activity | **Increasing** | State AGs gaining new tools, private class actions growing |
| Carrier-level call blocking | **Increasing** | STIR/SHAKEN adoption, analytics-based blocking becoming more aggressive |
| State-level AI disclosure laws | **Increasing** | Multiple states considering California-style bot disclosure requirements |
| Patent troll activity in AI | **Stable** | AI patent landscape is crowded but few enforcement actions against open-source tools |
| International regulatory alignment | **Increasing** | EU AI Act, similar frameworks emerging in UK, Canada, Australia |

---

## Sources

- [FCC AI Voice Ruling](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal)
- [Henson Legal: TCPA Fines for AI Platforms](https://www.henson-legal.com/ai-voice-compliance)
- [NCLC TCPA Developments 2024/2025](https://library.nclc.org/article/top-six-tcparobocall-developments-20242025)
- [FCC Caller ID Spoofing](https://www.fcc.gov/consumers/guides/spoofing)
- [FCC STIR/SHAKEN](https://www.fcc.gov/call-authentication)
