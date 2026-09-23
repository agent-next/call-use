# call-use v0.1.0 Launch Plan — CEO Review

**Date:** 2026-03-16
**Mode:** SCOPE EXPANSION
**Status:** Review complete, all decisions resolved

---

## Decisions Made

| # | Issue | Decision | Effort |
|---|---|---|---|
| 1 | Solo execution risk | Stagger launch across 2 days | Plan change |
| 2 | No conversion path | Zero-config GitHub Codespace sandbox | 1-2 hrs |
| 3 | API mismatch (task→instructions) | Fix all marketing materials | 30 min |
| 4 | Sandbox credential exposure | Proxy architecture (Cloudflare Worker) | 2-3 hrs |
| 5 | HN title choice | Use browser-use analogy | 5 min |
| 6 | Docs hosting resilience | Verify CDN-backed before T-7 | 15 min |
| D1 | Demo line | BUILD: Public Twilio number anyone can call | 2-3 hrs |
| D2 | GH Discussion thread | BUILD: "Show us what you called!" pinned thread | 10 min |
| D3 | CLI celebration | BUILD: ASCII art + star CTA on first call | 30 min |
| D4 | Plan B tweets | BUILD: 5 standalone viral-format tweets | 1 hr |
| D5 | Website widget | DEFER: Add to TODOS.md as vision item | — |
| T1 | Create TODOS.md | CREATE: With all deferred items from review | 30 min |
| T2 | 30-day community playbook | DEFER: Add to TODOS.md | — |

---

## Critical Findings

### Version Mismatch
- Plan says v0.1.0, actual build is v0.1.1
- Fix: Update all references in launch-plan.md and social-content.md

### API Parameter Mismatch
- Social content uses `task=` parameter
- Actual SDK uses `instructions=` parameter
- Fix: Update social-content.md, launch-plan.md, and all marketing assets

### "3 Lines" Claim
- Social posts say "3 lines of Python"
- README shows 6 lines; true minimum is 2 lines
- Fix: Make the code blocks in social content actually be 3 lines

### HN Title
- Recommended: `Show HN: Call-Use — The browser-use for phone calls (open-source, Python)`
- Rationale: browser-use has 55k+ stars; HN audiences respond to "the X for Y" framing

### Cost Framing
- Per-minute costs look scary in HN first comment
- Add: "Total cost for a typical 5-minute call: ~$0.15-0.25"

---

## Revised 2-Day Launch Sequence

### T-7: PRE-LAUNCH PREP (blockers)
- [ ] Build sandbox proxy (Cloudflare Worker) — rate limits, premium-rate blocking, emergency number blocking
- [ ] Build Codespace devcontainer.json + "Open in Codespace" README button
- [ ] Build demo phone line (inbound Twilio number + agent prompt)
- [ ] Fix API mismatch in all marketing materials (task → instructions)
- [ ] Fix version references (0.1.0 → 0.1.1)
- [ ] Update HN title to browser-use analogy
- [ ] Verify docs.call-use.com hosting is CDN-backed
- [ ] Draft 5 standalone Plan B tweets with visuals
- [ ] Build CLI first-call ASCII celebration + star CTA
- [ ] Create TODOS.md with deferred items
- [ ] Draft blog post (dev.to / hashnode)
- [ ] Claim social accounts (verify @calluse or @call_use)
- [ ] Identify + contact 10-15 early testers BY NAME
- [ ] Record updated demo video if API changed
- [ ] Test full funnel: post → GitHub → Codespace → sandbox call

### T-3: SEED CONTENT
- [ ] Send early access to 5-10 named contacts
- [ ] Teaser tweets
- [ ] Test sandbox proxy under load (10 concurrent calls)
- [ ] Confirm Product Hunt hunter or self-launch plan
- [ ] Draft HN first comment (include demo line number + cost framing)

### T-1: FINAL CHECKS (Pre-Flight Checklist)
- [ ] `pip install call-use` in clean venv → works
- [ ] `import call_use` → succeeds
- [ ] `call-use --version` → shows 0.1.1
- [ ] `call-use doctor` → validates setup
- [ ] Every README link resolves (200 status)
- [ ] Demo video plays on GitHub
- [ ] CI badge is green
- [ ] PyPI page has correct description
- [ ] call-use.com loads
- [ ] docs.call-use.com loads
- [ ] Codespace opens in <60 seconds
- [ ] Sandbox: first call succeeds
- [ ] Sandbox: 3-call rate limit works
- [ ] Sandbox: premium-rate number blocked
- [ ] Every code example in social posts runs without modification
- [ ] HN post text renders correctly (no markdown in plain text)
- [ ] Demo line answers and responds correctly
- [ ] Pre-schedule Day 1 tweets
- [ ] Verify PH listing is queued
- [ ] Purge CDN caches
- [ ] Create pinned GitHub Discussion: "Show us what you called!"

### T-0 DAY 1: HIGH-LEVERAGE CHANNELS
| Time (PT) | Action |
|-----------|--------|
| 00:01 | Product Hunt listing goes live |
| 06:00 | Show HN posted (browser-use analogy title) |
| 06:05 | HN first comment (include demo line number) |
| 06:15 | Twitter launch thread |
| 06:30 | Monitor HN (primary focus all day) |
| 09:00 | Respond to all HN/Twitter/GitHub comments |
| 12:00 | Midday check: respond everywhere |
| 14:00 | Stats tweet if traction ("100 stars in 6 hours") |
| 18:00 | Evening engagement round |
| 20:00 | Thank-you tweet |
| ALL DAY | If HN dead → fire Plan B standalone tweets at peak times |

### T-0 DAY 2: COMMUNITY & LONG-TAIL
| Time (PT) | Action |
|-----------|--------|
| 06:00 | r/Python |
| 06:30 | r/MachineLearning |
| 07:00 | r/LangChain |
| 07:30 | LinkedIn announcement |
| 08:00 | Discord communities (Latent Space, MLOps, AI Engineer) |
| 08:30 | dev.to tutorial article |
| 09:00 | r/artificial, r/LocalLLaMA, r/ChatGPT |
| 10:00 | Newsletter editor pitches |
| 12:00 | Respond to all Day 1 + Day 2 comments |
| 16:00 | r/programming |

### T+1 to T+7: Follow-up
- [ ] Respond to every GitHub issue and discussion
- [ ] Follow up on HN comments (peaks at 12-24 hours)
- [ ] Post "Day 1 stats" tweet
- [ ] Upvote and engage with Product Hunt comments
- [ ] Send follow-up DMs to influencers
- [ ] LinkedIn technical deep-dive post
- [ ] "How I built call-use" narrative article
- [ ] Twitter thread on architecture decisions
- [ ] Compile launch retrospective

---

## Rollback Plan

| IF | THEN |
|----|------|
| pip install broken | Fix + release 0.1.2 hotfix immediately |
| Sandbox proxy down | Disable "Open in Codespace" button, add "pip install" CTA |
| Website down | Cloudflare auto-recovery; if not, point DNS to GitHub Pages |
| Critical bug reported | Acknowledge publicly → fix → release → communicate |
| HN flagged/dead | Redirect energy to Plan B tweets + Reddit (Day 2 channels) |
| Twilio account suspended | Sandbox offline; core product works with user's own creds |
| Demo line overwhelmed | Per-caller rate limit; add "high demand" voicemail fallback |

---

## Security: Sandbox Proxy Requirements

The sandbox proxy (Cloudflare Worker) MUST enforce:
- Per-session rate limit: 3 calls max
- Per-call duration: 30 seconds max
- Per-IP rate limit: 10 calls/hour
- Block emergency numbers (911, 112, 999)
- Block premium-rate numbers (900, 976)
- Block Caribbean/Pacific NPAs (existing phone.py logic)
- Real credentials held server-side only (never exposed to Codespace)
- Basic alerting: error rate >5%, latency >2s

---

## Observability: Launch Day Dashboard

Monitor on T-0:
- GitHub stars (real-time via API)
- HN post position (hnrankings.info or manual)
- Twitter thread impressions
- Product Hunt upvotes
- Sandbox proxy: calls made, errors, rate limit triggers
- Demo line: calls received
- GitHub issues opened
- Codespace creation rate

---

## Failure Modes Registry

| Codepath | Failure Mode | Rescued? | Test? | User Sees? | Logged? |
|---|---|---|---|---|---|
| Sandbox proxy | Twilio timeout | Y | Y | "Unavailable" | Y |
| Sandbox proxy | 50 concurrent calls | ? | N ← GAP | Silent? | N |
| Demo line | Agent hallucination | N | N | Bad response | Y |
| Codespace | Build timeout | N | N ← GAP | Error page | N |
| pip install | Dep conflict | N | Y* | Import error | N |
| HN post | Zero engagement | Y | N/A | Plan B tweets | N/A |

**CRITICAL GAPS**: Sandbox concurrent load handling (add load test at T-3) and Codespace build timeout (add monitoring).

---

## NOT in Scope

1. Inbound call support — v0.2 feature
2. International numbers — v0.2
3. Interactive website widget — deferred to TODOS.md
4. Claude/Anthropic LLM support — future work
5. Contributor onboarding guide — post-launch (T+7)
6. 30-day community playbook — deferred to TODOS.md
7. Podcast pitches — execute if time permits at T+2-3

---

## What Already Exists

| Sub-problem | Existing Asset | Status |
|---|---|---|
| Demo video | `docs/assets/demo.mp4` | Ready |
| Website | `../call-use-web/` (Astro + Cloudflare) | Ready |
| README | Polished, badges, code examples | Needs version fix |
| Social content | `launch/social-content.md` | Needs API fix |
| Email templates | `launch/email-templates.md` | Ready |
| Press kit | `launch/press-kit.md` | Ready |
| FAQ | `launch/launch-faq.md` | Ready |
| Outreach list | `launch/outreach.md` | Ready |
| Competitor analysis | `competitor-analysis.md` + `pine-ai-comparison.md` | Ready |
| CLI setup wizard | `call-use setup` / `call-use doctor` | Ready |
| Phone validation | `call_use/phone.py` | Ready |
| BDD test suite | 94 tests across 7 domains | Ready |

---

## T-7 Deliverables Summary

| # | Deliverable | Effort | Priority |
|---|---|---|---|
| 1 | Sandbox proxy (Cloudflare Worker) | 2-3 hrs | P0 |
| 2 | Codespace devcontainer.json | 1-2 hrs | P0 |
| 3 | Demo phone line (inbound) | 2-3 hrs | P1 |
| 4 | Fix API mismatch in marketing | 30 min | P0 |
| 5 | Fix version references | 15 min | P0 |
| 6 | Update HN title | 5 min | P0 |
| 7 | Verify docs hosting (CDN) | 15 min | P1 |
| 8 | Draft 5 Plan B tweets | 1 hr | P1 |
| 9 | CLI first-call celebration | 30 min | P2 |
| 10 | Create TODOS.md | 30 min | P1 |
| 11 | Create GitHub Discussion | 10 min | P2 |

**Total new effort: ~10-12 hours**

---

## Dream State Delta

```
  AFTER THIS PLAN                    12-MONTH IDEAL              GAP
  ────────────────                   ──────────────              ────
  500 stars, 200 installs            5,000+ stars, 5K+           Sustained community
  50 community members               installs, active            engagement post-launch.
  Awareness established              contributors, framework     Sandbox → hosted
  Zero-config sandbox live           integrations standard,      playground evolution.
  Demo line operational              hosted service option,      Positioning may need
  browser-use positioning            international support,      to evolve from "tool-
  locked in                          inbound calls               use layer" to "voice
                                                                 AI platform."
```
