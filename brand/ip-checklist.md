# call-use Intellectual Property Protection Checklist

---

## 1. Trademark Registration

### Pre-filing Search

- [ ] Search USPTO TESS database for "call-use" and similar marks (calluse, call use, calluse.ai)
- [ ] Search state trademark databases in primary operating states
- [ ] Search international trademark databases (WIPO, EUIPO) if international use is planned
- [ ] Check for common-law usage via web search -- look for existing products/services using "call-use"
- [ ] Document search results with dates for the filing record

### USPTO Filing

**Recommended classes:**

| Class | Description | Covers |
|-------|-------------|--------|
| Class 9 | Computer software | Downloadable software for telephony automation, AI agent frameworks |
| Class 42 | SaaS / technology services | Hosted services, API access, cloud platform (if applicable) |

**Filing basis:** Use Intent-to-Use (Section 1(b)) if the product is not yet commercially available. Convert to use-based (Section 1(a)) once launched.

**Mark format:** Standard character mark "call-use" (covers any stylization). Optionally file a design mark for the logo separately.

**Estimated costs:**

| Item | Cost (USD) | Notes |
|------|-----------|-------|
| USPTO filing fee (per class, TEAS Plus) | $250 | x2 classes = $500 |
| Attorney fees (optional but recommended) | $1,000 - $2,500 | For search + filing |
| Statement of Use fee | $100/class | Due after Intent-to-Use allowance |
| Total (self-file, 2 classes) | ~$700 | |
| Total (with attorney, 2 classes) | ~$2,000 - $3,200 | |

**Estimated timeline:**

| Milestone | Timeframe |
|-----------|-----------|
| Filing to initial review | 3-4 months |
| Examination / Office Actions | 4-8 months |
| Publication for opposition | 30-day window |
| Registration (if no opposition) | 10-14 months total |
| Intent-to-Use: Statement of Use deadline | 6 months after allowance (extendable to 36 months) |

### International Considerations

- If targeting international markets, consider Madrid Protocol filing (extends US registration internationally)
- Priority: US first. Evaluate EU (EUIPO) and UK (UKIPO) if user base justifies it
- Madrid Protocol filing window: 6 months from US filing date to claim priority

---

## 2. Copyright

### What MIT License Covers

The MIT license applies to the **source code** of the call-use runtime. It permits:

- Commercial and non-commercial use
- Modification and distribution
- Private use
- Sublicensing

It requires:

- Copyright notice and license text included in copies/substantial portions

### What MIT License Does NOT Cover

| Asset | Protection | Notes |
|-------|-----------|-------|
| Logo / icon | Trademark + Copyright | Not covered by MIT; separate IP |
| Brand name "call-use" | Trademark | MIT does not grant trademark rights |
| Documentation text | Copyright (auto) | MIT covers code; docs may have separate terms |
| Brand guidelines | Copyright (auto) | Not open source; proprietary brand asset |
| Website design | Copyright (auto) | Separate from the runtime code |

### Recommended Copyright Notices

**In source code files:**
```
Copyright (c) 2026 agent-next contributors
Licensed under the MIT License. See LICENSE for details.
```

**In brand assets (this repo):**
```
Copyright (c) 2026 agent-next. All rights reserved.
The call-use name, logo, and brand assets are trademarks of agent-next
and are NOT covered by the MIT license of the call-use runtime.
```

---

## 3. Domain Portfolio

### Core Domains

| Domain | Purpose | Action |
|--------|---------|--------|
| `call-use.com` | Primary website | Registered |
| `docs.call-use.com` | Documentation | Subdomain of primary |
| `call-use.dev` | Developer portal / redirect | Register to protect |
| `call-use.ai` | AI-focused alternate | Register to protect |
| `call-use.io` | Tech alternate | Register if budget allows |
| `calluse.com` | Typo protection | Register if available |

### Domain Actions

- [ ] Verify `call-use.com` registration and auto-renewal
- [ ] Register `call-use.dev` (Google Domains / Squarespace)
- [ ] Register `call-use.ai` if available
- [ ] Set up DNS for `docs.call-use.com` subdomain
- [ ] Enable WHOIS privacy on all domains
- [ ] Set up domain monitoring / alerts for similar registrations

---

## 4. Package Name Protection

### PyPI

- [ ] Register `call-use` package on PyPI (even if placeholder)
- [ ] Register `calluse` as alternate (if available) -- redirect or reserve
- [ ] Set up PyPI organization account under `agent-next`
- [ ] Enable 2FA on PyPI account
- [ ] Add trusted publishers (GitHub Actions OIDC) for secure releases

### npm (if JS/TS SDK planned)

- [ ] Register `call-use` package on npm
- [ ] Register `@agent-next/call-use` scoped package
- [ ] Enable 2FA on npm account

### Other Registries

- [ ] Conda-forge: register when package is stable
- [ ] Homebrew: create tap when CLI tool is ready
- [ ] Docker Hub: reserve `agentNext/call-use` or `calluse` image name

---

## 5. Social Handle Claims

| Platform | Handle | Action |
|----------|--------|--------|
| GitHub | `agent-next/call-use` | Create repo |
| Twitter/X | `@calluse` | Claim |
| Twitter/X | `@call_use` | Claim (backup) |
| Reddit | `r/calluse` | Create subreddit |
| Discord | `call-use` | Create server |
| LinkedIn | `call-use` | Create company page |
| YouTube | `@calluse` | Claim handle |
| Hacker News | Submit launch post | Plan for launch day |
| Product Hunt | `call-use` | Reserve listing |

---

## 6. Contributor License Agreement (CLA)

### Recommendation: Lightweight CLA

For an MIT-licensed open-source project, a full CLA is often overkill and can deter contributors. Recommended approach:

**Option A: Developer Certificate of Origin (DCO) -- Recommended**

Use the Linux Foundation's DCO instead of a CLA. Contributors sign off on each commit:

```
Signed-off-by: Developer Name <developer@example.com>
```

This certifies the contribution is original or properly licensed. Enforced via:
- GitHub App: [DCO Bot](https://github.com/apps/dco)
- Git hook: `git commit -s`

**Option B: CLA (if stronger IP assignment is needed later)**

Use a lightweight CLA like the Apache Individual CLA or the Contributor License Agreement from GitHub. Enforce with:
- [CLA Assistant](https://cla-assistant.io/) GitHub App
- One-time signature per contributor

### CLA Decision Matrix

| Factor | DCO | Full CLA |
|--------|-----|----------|
| Contributor friction | Low | Medium |
| Legal strength | Moderate | Strong |
| Relicensing ability | No | Yes |
| Community perception | Positive | Mixed |
| Setup effort | Minimal | Moderate |

**Recommendation:** Start with DCO. Upgrade to CLA only if relicensing or dual-licensing becomes a business need.

---

## 7. Trademark Policy for Forks and Derivatives

### Permitted Uses (no permission needed)

- Referring to call-use by name in documentation, blog posts, talks, and comparisons
- Stating that a project is "based on call-use" or "compatible with call-use"
- Using the call-use name in package dependency metadata
- Academic or journalistic references

### Requires Permission

- Using the call-use name or logo in a product name (e.g., "SuperCallUse")
- Using the call-use logo on merchandise
- Implying official endorsement or affiliation
- Using the call-use name in a domain name (e.g., "calluse-pro.com")

### Forks

Forks of the MIT-licensed code may:
- Use and modify the source code freely
- NOT use the "call-use" name, logo, or branding for their fork
- Must rename and rebrand if distributing a modified version as a distinct product
- May state "forked from call-use" for attribution

### Template Policy Statement

```
The call-use name and logo are trademarks of agent-next. The MIT license
for the call-use source code does not grant permission to use these
trademarks. Forks and derivative works must use a different name and logo.
You may state that your project is "based on call-use" or "forked from
call-use" for factual attribution.

For questions about trademark usage, contact: legal@call-use.com
```

---

## 8. Brand Usage Guidelines Summary

### Logo Usage

| Usage | Allowed? |
|-------|----------|
| Linking to call-use in a blog post with the logo | Yes |
| Using the logo in a presentation about call-use | Yes |
| Modifying the logo colors or shape | No |
| Using the logo to imply endorsement of your product | No |
| Including the logo in competing products | No |

### Name Usage

| Usage | Allowed? |
|-------|----------|
| "Built with call-use" | Yes |
| "Powered by call-use" | Yes |
| "call-use certified" | No (without permission) |
| "call-use" as part of your product name | No (without permission) |

---

## 9. Action Items (Priority Order)

### Immediate (before public launch)

- [ ] Register `call-use` on PyPI
- [ ] Claim social handles (Twitter, Discord)
- [ ] Register `call-use.dev` domain
- [ ] Add trademark notice to brand assets repo
- [ ] Set up DCO enforcement on GitHub repos
- [ ] Add LICENSE file (MIT) to code repos
- [ ] Add brand usage policy to website

### Within 30 days of launch

- [ ] File USPTO trademark application (Class 9 + Class 42)
- [ ] Register `call-use.ai` domain
- [ ] Set up trusted publishers on PyPI
- [ ] Create CONTRIBUTING.md with DCO instructions
- [ ] Publish brand guidelines on website

### Within 90 days of launch

- [ ] Monitor trademark application progress
- [ ] Set up Google Alerts for "call-use" brand monitoring
- [ ] Evaluate international trademark filing needs
- [ ] Review and update brand guidelines based on community feedback
- [ ] Audit unauthorized uses of brand name/logo
