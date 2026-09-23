# call-use Platform Liability Analysis

> Last updated: 2026-03-14

Analysis of call-use's legal liability as both an open-source tool and a potential hosted service provider.

**Disclaimer**: This analysis is informational only and does not constitute legal advice. Consult a licensed attorney for specific liability questions.

---

## 1. Section 230 Considerations

### 1.1 Does Section 230 Apply to call-use?

**Likely not in a meaningful way.**

Section 230 of the Communications Decency Act (47 U.S.C. Section 230) provides immunity to "interactive computer services" from liability for content provided by third-party users. However, several factors limit its applicability to call-use:

1. **Telephony exemption**: Section 230 explicitly does not affect "any law relating to... communications privacy law" — the TCPA is a communications law, and courts have held that Section 230 does not immunize platforms from TCPA liability.

2. **Not a passive intermediary**: call-use is not merely hosting third-party content. It actively generates AI voice content using GPT-4o and initiates outbound calls. When AI generates the conversation, the platform may be viewed as a content creator rather than a passive intermediary.

3. **Criminal law carve-out**: Section 230 provides no immunity against federal criminal statutes. If call-use were used for fraud (e.g., AI voice phishing), Section 230 would not shield the platform.

4. **AI content generation debate**: There is growing legal consensus that platforms generating content via AI cannot claim Section 230 immunity for that content. The platform is effectively "manufacturing the content output via its algorithms," not merely transmitting user-generated content.

### 1.2 Precedent

- **Duguid v. Facebook (2021)**: While primarily about ATDS definition, this case confirmed that tech platforms are subject to TCPA.
- **ACA International v. FCC (2018)**: Clarified that the FCC's broad autodialer definition was invalid, but the underlying TCPA obligations remain.
- No direct precedent exists for open-source calling tool liability, making this an area of legal uncertainty.

---

## 2. Common Carrier vs. Content Creator Analysis

### 2.1 Where Does call-use Fall?

| Factor | Common Carrier (Phone Company) | Content Creator | call-use |
|--------|-------------------------------|----------------|----------|
| Generates content | No | Yes | **Yes** (AI generates speech) |
| Controls who can use service | Limited | Yes | **Partial** (open-source, but hosted version can control) |
| Routes/transmits content | Yes | No | **Yes** (via Twilio SIP) |
| Modifies content in transit | No | Yes | **Yes** (AI generates responses dynamically) |
| Subject to TCPA | Yes (different obligations) | Yes | **Yes** |

**Assessment**: call-use is **not** a common carrier. It is closer to a content creator or application platform because it generates the AI conversation content. Common carrier protections (47 U.S.C. Section 202) do not apply.

However, call-use is also not purely a content creator — it is a **tool** that users deploy. The closest analogues are:
- **Twilio** — provides telephony APIs but does not generate content (platform/tool)
- **Bland.ai / Vapi / Retell** — provide AI calling platforms (SaaS with user-generated campaigns)
- **Email marketing tools** (Mailchimp, SendGrid) — provide the infrastructure, users create the content

### 2.2 Steps to Reduce Platform Liability

1. **Do not generate call content**: call-use provides the AI engine, but users define the prompts, target numbers, and campaign parameters. Emphasize this in documentation and ToS.
2. **Require user acknowledgment**: Before using the platform, users must acknowledge their legal obligations.
3. **Implement abuse controls**: Rate limiting, number verification, content moderation for the hosted version.
4. **Maintain logs**: For the hosted version, maintain records that can identify which user initiated which calls.
5. **Respond to complaints promptly**: Implement a clear abuse reporting process.

---

## 3. Open-Source Liability

### 3.1 MIT License Protection

call-use is distributed under the MIT License, which includes the standard disclaimer:

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY.

### 3.2 Does Open-Source Distribution Shift Liability?

**Largely yes, for self-hosted deployments.**

When users self-host call-use:
- They operate the software on their own infrastructure
- They use their own Twilio and OpenAI API keys
- They define the calling campaigns and targets
- They are the "caller" under TCPA, not the software author

**Analogy to dual-use tools:**

| Tool | Legal Status | Precedent |
|------|-------------|-----------|
| **nmap** | Legal to distribute; illegal use is user's liability | No prosecution of nmap developers for users' port scanning |
| **Metasploit** | Legal to distribute; used by both security professionals and attackers | Rapid7 (maintainer) not liable for malicious use |
| **Kali Linux** | Legal distribution of penetration testing tools | Offensive Security not liable for criminal use |
| **Asterisk** (open-source PBX) | Legal; used for legitimate and illegitimate calling | Digium/Sangoma not liable for robocall abuse |
| **call-use** | Should follow same pattern | No precedent yet |

**Key factors protecting open-source authors:**
1. No control over how users deploy the software
2. No knowledge of specific illegal uses
3. Software has substantial legitimate uses (appointment reminders, customer service, accessibility)
4. MIT license disclaims warranty and liability
5. No revenue from illegal use (unlike a hosted service)

### 3.3 Limits of Open-Source Protection

Open-source distribution does **not** protect against:
- **Inducement liability**: If the software is marketed primarily for illegal use (see *MGM Studios v. Grokster*). call-use must be positioned for legitimate use.
- **Aiding and abetting**: If the developers have actual knowledge of specific illegal use and actively facilitate it.
- **Product liability**: Some jurisdictions are developing product liability theories for software. This is an evolving area.
- **Export control**: If the software includes encryption (it uses TLS for SIP), export control regulations may apply (though standard encryption is generally exempt under EAR Section 740.17).

---

## 4. Hosted Trial Liability

### 4.1 Increased Liability

Operating a hosted version of call-use **significantly increases liability** compared to open-source distribution alone:

| Factor | Self-Hosted (User) | Hosted Trial (call-use) |
|--------|-------------------|------------------------|
| Who operates the infrastructure? | User | call-use |
| Who originates the call? | User (via their Twilio) | Shared infrastructure (call-use's Twilio) |
| TCPA "caller" liability | User | **Potentially shared** |
| Knowledge of call content | User only | call-use has access |
| Ability to prevent abuse | User's responsibility | **call-use's responsibility** |
| Regulatory exposure | User | **call-use + User** |

**Critical risk**: When call-use operates the Twilio account, it may be deemed a co-originator of calls under the TCPA. The FCC has held that entities who "initiate" calls — including those who provide the means to make the call — can be jointly liable.

### 4.2 Terms of Service Requirements

The hosted trial **must** have comprehensive Terms of Service covering:

1. **User eligibility** — age, jurisdiction, business registration
2. **Acceptable Use Policy** — what users can and cannot do
3. **Compliance acknowledgment** — users must affirm they understand and will comply with TCPA, TSR, and state laws
4. **Consent documentation** — users must certify they have proper consent for all numbers called
5. **Indemnification** — users indemnify call-use for all claims arising from their use
6. **Limitation of liability** — cap call-use's liability (industry standard: $100 or fees paid)
7. **Data handling** — how call transcripts, recordings, and PII are processed, stored, and deleted
8. **Termination** — call-use's right to terminate accounts for violations, without notice
9. **Dispute resolution** — arbitration clause, governing law, venue

### 4.3 Acceptable Use Policy Requirements

The AUP must explicitly prohibit:

- Calls without prior express consent
- Calls to DNC-registered numbers (without valid exemption)
- Caller ID spoofing
- Impersonation (AI pretending to be a specific real person)
- Fraud, phishing, or social engineering
- Harassment, threats, or abuse
- Calls outside permitted hours
- Political robocalls (additional regulations apply)
- Debt collection (FDCPA adds another layer of regulation)
- Healthcare-related calls without HIPAA compliance

### 4.4 Handling Abuse Reports

**Required process:**
1. Publish an abuse reporting endpoint (email: abuse@call-use.com, web form)
2. Acknowledge reports within **24 hours**
3. Investigate within **48 hours**
4. Suspend offending accounts immediately if evidence of illegal use
5. Cooperate with law enforcement if subpoenaed
6. Maintain abuse report records for **3 years minimum**

**Proactive monitoring:**
- Rate limiting (maximum calls per hour/day per account)
- Content monitoring for fraud indicators
- Caller ID validation
- Geographic restrictions during off-hours
- Anomaly detection (sudden volume spikes)

---

## 5. Comparison: How Similar Platforms Handle Liability

### 5.1 Retell AI

- **Most comprehensive approach** among AI calling platforms
- Explicit TCPA compliance section in ToS (Section 4.2)
- Requires users to maintain consent proof for 5 years
- Requires DNC scrubbing every 31 days
- Requires AI voice disclosure at call beginning
- Prohibits use of real people's voices without consent
- User indemnification covers TCPA violations and regulatory fines

### 5.2 Vapi

- References TCPA in indemnification clause
- Requires users to comply with applicable laws including TCPA
- HIPAA/PCI compliance requires specific configuration
- Less detailed than Retell on calling-specific compliance

### 5.3 Bland.ai

- **Notable gap**: No specific TCPA disclaimers in Terms of Service
- Standard software disclaimers (AS IS, $100 liability cap)
- General prohibition on illegal use
- No calling-specific compliance guidance in ToS

### 5.4 Recommendation for call-use

Follow **Retell's approach** as a model — it is the most thorough and provides the strongest legal protection. Key elements to adopt:
- Explicit TCPA compliance section
- Specific prohibited calling behaviors
- Consent documentation requirements
- AI voice disclosure requirements
- DNC scrubbing obligations
- User indemnification for regulatory violations

---

## 6. Recommendations

### 6.1 Terms of Service Template Outline

See `tos-outline.md` for the complete outline.

### 6.2 Acceptable Use Policy Template Outline

**Section 1: Purpose**
- This AUP governs use of the call-use hosted service
- Violations may result in immediate termination

**Section 2: Permitted Uses**
- Legitimate business communications with proper consent
- Appointment reminders, customer service, notifications
- Sales/marketing calls with prior express written consent

**Section 3: Prohibited Uses**
- [Full list — see Section 4.3 above]

**Section 4: User Obligations**
- Maintain consent records
- Honor DNC requests
- Disclose AI nature
- Comply with recording laws
- Display accurate caller ID

**Section 5: Enforcement**
- Monitoring and investigation
- Suspension and termination
- Cooperation with authorities

### 6.3 Required Disclaimers

**README/documentation disclaimer**: See `legal-disclaimer.md`.

**In-app disclaimer** (displayed before first use):
> By using call-use, you acknowledge that you are solely responsible for complying with the Telephone Consumer Protection Act (TCPA), the Telemarketing Sales Rule (TSR), the Truth in Caller ID Act, FCC regulations regarding AI-generated voice calls, and all applicable state and local laws. You certify that you have obtained proper consent from all parties you call and will honor all Do Not Call requests.

### 6.4 User Acknowledgment Requirement

**Strongly recommended** for both self-hosted and hosted versions:

- **Self-hosted**: Display legal notice during installation/setup. Include in README prominently.
- **Hosted trial**: Require checkbox acknowledgment of legal obligations before account activation. Store the timestamp and text of the acknowledgment.

---

## Sources

- [IAPP: AI and Platform Liability Laws in the U.S.](https://iapp.org/news/a/ai-and-digital-governance-platform-liability-laws-in-the-u-s)
- [Section 230 Overview](https://en.wikipedia.org/wiki/Section_230)
- [Henson Legal: AI Voice Agent TCPA Liability](https://www.henson-legal.com/ai-voice-compliance)
- [Retell AI Terms of Service](https://www.retellai.com/legal/terms-of-service)
- [Vapi Terms of Service](https://vapi.ai/terms-of-service)
- [Bland AI Terms of Service](https://www.bland.ai/legal/terms-of-service)
- [ABA: Section 230 and AI](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-november/beyond-search-bar-generative-ai-section-230-tightrope-walk/)
- [Mayer Brown: FCC AI Call Regulation](https://www.mayerbrown.com/en/insights/publications/2024/02/fcc-declares-authority-and-intent-to-regulate-ai-generated-calls-under-the-tcpa)
