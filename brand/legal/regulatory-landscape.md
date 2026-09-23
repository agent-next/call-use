# Regulatory Landscape for AI-Powered Automated Calling

> Last updated: 2026-03-14

This document covers the legal and regulatory framework applicable to call-use, an open-source tool that enables AI agents to make automated outbound phone calls via Twilio SIP and GPT-4o.

---

## 1. US Federal Laws

### 1.1 Telephone Consumer Protection Act (TCPA) — 47 U.S.C. Section 227

The TCPA is the primary federal law governing automated and prerecorded calls. It is the single most important statute for call-use users.

#### Key Provisions

- **Prior Express Consent**: Calls using an "artificial or prerecorded voice" to residential lines require prior express consent. Marketing calls require **prior express written consent (PEWC)**.
- **Autodialer (ATDS) Definition**: The TCPA restricts calls made using an "automatic telephone dialing system" — defined as equipment with the capacity to store or produce telephone numbers using a random or sequential number generator and to dial such numbers. After *Facebook v. Duguid* (2021), the Supreme Court narrowed this to systems that actually generate random/sequential numbers, not simply systems that dial from a stored list.
- **AI Voices = "Artificial"**: On **February 8, 2024**, the FCC unanimously adopted a **Declaratory Ruling (FCC 24-17)** confirming that AI-generated voices constitute "artificial" voices under the TCPA. This means all TCPA restrictions on artificial/prerecorded voice calls apply to AI-generated speech — including call-use's GPT-4o voice output.
- **Consent Revocation**: As of **April 11, 2025**, opt-out requests must be processed within **10 business days** (reduced from 30).
- **Calling Hours**: Calls to residential numbers are restricted to **8:00 AM - 9:00 PM local time** of the called party.

#### Does call-use Qualify as an ATDS?

Likely **no** under the narrow *Duguid* definition — call-use dials specific numbers provided by the user, not random/sequential numbers. However, the AI voice output **independently triggers TCPA obligations** regardless of autodialer status, because the FCC's February 2024 ruling classifies AI voices as "artificial."

#### Penalties

- **$500 per violation** (per call)
- **$1,500 per willful violation** (treble damages)
- Private right of action (individuals can sue)
- State AG enforcement authority
- In 2024, an Oregon jury awarded **$925 million** in a mass robocalling case

#### Key References

- [FCC Declaratory Ruling on AI Voices (Feb 2024)](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal)
- [FCC 24-17 Full Text](https://docs.fcc.gov/public/attachments/FCC-24-17A1.pdf)
- *Facebook, Inc. v. Duguid*, 592 U.S. ___ (2021)

---

### 1.2 Telemarketing Sales Rule (TSR) — 16 C.F.R. Part 310

The FTC's TSR applies when calls involve the sale of goods or services (telemarketing). **All TSR provisions extend to AI-enabled calls.**

#### Key Provisions

- **Do Not Call Registry**: Telemarketers must not call numbers on the National DNC Registry. They must scrub their call lists against the registry at least every **31 days**.
- **AI Voice Cloning**: The FTC has affirmed that TSR prohibitions cover robocalls using voice cloning technology (March 2024 update).
- **Caller Identification**: Telemarketers must transmit caller ID information and display a phone number that the consumer can call back.
- **Call Abandonment**: Telemarketers may not abandon more than 3% of outbound calls per campaign per 30-day period.
- **Calling Hours**: 8:00 AM - 9:00 PM local time.
- **B2B Exception Removed**: As of the 2024 amendments, the TSR's exception for business-to-business calls has been narrowed. B2B calls involving AI or prerecorded voices face new recordkeeping requirements.

#### When Does a call-use Call Count as Telemarketing?

A call is telemarketing under the TSR if its purpose is to induce the purchase of goods or services. Informational calls (appointment reminders, status updates, surveys) are generally **not** telemarketing. However, if the call includes any sales pitch or up-sell, it becomes subject to TSR requirements.

#### Recordkeeping

The TSR requires telemarketers to maintain records for **5 years**, including:
- Advertising and promotional materials
- Prize/gift records
- Sales records
- Employee/contractor records
- Records of AI voices used in telemarketing conversations

#### Key References

- [FTC Telemarketing Sales Rule](https://www.ftc.gov/legal-library/browse/rules/telemarketing-sales-rule)
- [FTC March 2024 AI Protections](https://www.ftc.gov/news-events/news/press-releases/2024/03/ftc-implements-new-protections-businesses-against-telemarketing-fraud-affirms-protections-against-ai)

---

### 1.3 TRACED Act (Pallone-Thune Telephone Robocall Abuse Criminal Enforcement and Deterrence Act)

The TRACED Act (2019) strengthened enforcement against illegal robocalls and mandated the STIR/SHAKEN caller ID authentication framework.

#### Key Requirements

- **STIR/SHAKEN**: Voice service providers must implement the STIR/SHAKEN framework to authenticate caller ID. As of **September 18, 2025**, all providers must sign calls using their own digital certificates (no third-party certificates).
- **Robocall Mitigation Database (RMD)**: All voice service providers must file certifications and robocall mitigation plans in the FCC's RMD. Since **May 28, 2024**, providers must block traffic from entities not listed in the RMD.
- **Extended Statute of Limitations**: The TRACED Act extended the statute of limitations for TCPA enforcement from 1 year to **4 years**.
- **Increased Penalties**: Fines up to **$10,000 per violation** for intentional violations.

#### Implications for call-use

call-use users route calls through Twilio, which is a registered voice service provider with STIR/SHAKEN implementation. The TRACED Act obligations primarily fall on Twilio as the originating carrier. However, if a user's calls are flagged as spam/robocalls, Twilio may terminate their account, and downstream carriers may block the calls.

#### Key References

- [FCC TRACED Act Implementation](https://www.fcc.gov/TRACEDAct)
- [STIR/SHAKEN Authentication](https://www.fcc.gov/call-authentication)

---

### 1.4 Truth in Caller ID Act — 47 U.S.C. Section 227(e)

#### Key Provisions

- It is **illegal** to transmit misleading or inaccurate caller ID information **with intent to defraud, cause harm, or wrongly obtain anything of value**.
- Penalties: Up to **$10,000 per violation**, not to exceed **$1,000,000 total**.
- Legitimate uses (e.g., displaying a business number instead of a personal number) are permitted.

#### Implications for call-use

call-use users must display accurate caller ID. Twilio enforces this to a degree (requiring verified numbers), but users must not configure caller ID to deceive recipients about the identity of the caller.

#### Key References

- [FCC Caller ID Spoofing Guide](https://www.fcc.gov/consumers/guides/spoofing)

---

### 1.5 FCC Regulations — 2024-2025 Developments

#### February 2024: AI Voices Declaratory Ruling

The FCC unanimously ruled that AI-generated voices are "artificial" under the TCPA. Key implications:

1. **Prior express consent required** for all AI voice calls to residential lines
2. **Prior express written consent required** for AI voice marketing calls
3. **State AG enforcement** — the ruling gives state attorneys general new tools to pursue AI robocall violations
4. **Immediate effect** — no grace period was provided

#### September 2024: FCC Notice of Inquiry on AI in Telecommunications

The FCC opened a broader inquiry into AI's implications for consumer protection in telecommunications (Docket No. 24-220), exploring:
- Whether additional rules are needed for AI-generated content in calls
- How to address AI-powered scam calls
- Whether disclosure requirements should be expanded

#### April 2025: Opt-Out Rule Takes Effect

New requirements for processing consent revocations within 10 business days (down from 30).

---

## 2. US State Laws

### 2.1 Two-Party Consent States (Call Recording)

If call-use records calls (which it does for transcription), users **must** comply with recording consent laws. In two-party (all-party) consent states, **all parties** must be informed and consent to recording.

**Two-party consent states (13 states):**

| State | Statute |
|-------|---------|
| California | Cal. Penal Code Section 632 |
| Connecticut | Conn. Gen. Stat. Section 52-570d |
| Delaware | Del. Code tit. 11, Section 2402 |
| Florida | Fla. Stat. Section 934.03 |
| Illinois | 720 ILCS 5/14-2 |
| Maryland | Md. Code, Cts. & Jud. Proc. Section 10-402 |
| Massachusetts | Mass. Gen. Laws ch. 272, Section 99 |
| Michigan | Mich. Comp. Laws Section 750.539c |
| Montana | Mont. Code Ann. Section 45-8-213 |
| Nevada | Nev. Rev. Stat. Section 200.620 |
| New Hampshire | N.H. Rev. Stat. Ann. Section 570-A:2 |
| Pennsylvania | 18 Pa.C.S. Section 5704 |
| Washington | Wash. Rev. Code Section 9.73.030 |

**All other states (37 + DC)** are one-party consent — only one party needs to consent.

**Interstate calls**: When a call crosses state lines, the **stricter** law typically applies. A call from Texas (one-party) to California (two-party) should follow California's all-party consent requirement.

### 2.2 California

- **Cal. Penal Code Section 632**: Illegal to record confidential communications without consent of all parties. Penalties: fine up to **$2,500** and/or imprisonment up to one year; civil damages of **$5,000 per violation**.
- **California Bot Disclosure Law (SB 1001)**: Requires disclosure when a bot is used to communicate with a person to influence a commercial transaction or voting. Penalties: **$500 per undisclosed AI interaction**.
- **CCPA/CPRA**: If call-use processes personal information of California residents, users must comply with data access, deletion, and opt-out rights. Call recordings and transcripts containing personal information are covered.
- **California Robocall Laws**: California law mirrors federal TCPA restrictions and adds state-specific penalties.

### 2.3 Florida

- **Two-party consent state** for recording (Fla. Stat. Section 934.03). Criminal penalties for violations (third-degree felony).
- **Florida Telephone Solicitation Act (Fla. Stat. Section 501.059)**: Requires written consent for automated calls. Strict restrictions on telemarketing hours and practices.
- **Private right of action** with statutory damages of $500 per violation.

### 2.4 New York

- **One-party consent** for recording (N.Y. Penal Law Section 250.00).
- **New York Telemarketing Law (GBL Section 399-z)**: Requires Do Not Call compliance. Telemarketers must register with the state.
- **NYC Local Laws**: Additional restrictions may apply for calls to NYC residents.

### 2.5 Texas

- **One-party consent** for recording (Tex. Penal Code Section 16.02).
- **Texas Business & Commerce Code Section 304**: Regulates automated calls. Requires express written consent for prerecorded marketing calls.
- **State TCPA analogue**: Texas has its own TCPA-like provisions with separate enforcement.

### 2.6 States with the Strictest Robocall Laws

1. **California** — Two-party consent + bot disclosure + CCPA + aggressive AG enforcement
2. **Florida** — Two-party consent + strict telemarketing act + criminal penalties for recording violations
3. **Washington** — Two-party consent + Consumer Protection Act enforcement
4. **Illinois** — Two-party consent + Biometric Information Privacy Act (BIPA) if voice biometrics are used
5. **Massachusetts** — Two-party consent + strict wiretapping statute (all-party, no exceptions)

---

## 3. International Regulations (Future Expansion)

### 3.1 European Union

#### GDPR (General Data Protection Regulation)

- Voice data is **personally identifiable information (PII)** — any processing (recording, transcription, storage) requires a lawful basis.
- **Consent** must be freely given, specific, informed, and unambiguous.
- **Data subject rights**: Access, erasure ("right to be forgotten"), portability, objection to processing.
- **Data protection impact assessment (DPIA)** likely required for automated calling at scale.
- **Penalties**: Up to **EUR 20 million** or **4% of global annual revenue**, whichever is higher.

#### ePrivacy Directive (2002/58/EC)

- **Automated calling systems** for direct marketing require **opt-in consent** (Article 13).
- Even human-operated marketing calls are restricted in many member states.
- AI voice calls would almost certainly be classified as "automated calling systems."

#### EU AI Act (2024)

- Voicebots are classified as **"limited risk"** systems requiring:
  - Clear disclosure that the caller is an AI
  - Maintaining logs and documentation of interactions
  - Option to transfer to a human agent
- Higher-risk classifications may apply if the system is used for credit scoring, employment, or law enforcement.

### 3.2 United Kingdom

- **Privacy and Electronic Communications Regulations (PECR)**: Automated marketing calls require opt-in consent. Live marketing calls must check the Telephone Preference Service (TPS).
- **ICO (Information Commissioner's Office)**: Enforces PECR and UK GDPR. Can issue fines up to GBP 500,000 under PECR.
- **UK GDPR**: Mirrors EU GDPR post-Brexit with UK-specific enforcement.

### 3.3 Canada

- **CRTC Unsolicited Telecommunication Rules (UTRs)**: Govern telemarketing calls. CASL (Canada's Anti-Spam Legislation) does **not** directly apply to voice calls — voice calls are regulated under the UTRs.
- **National DNCL (Do Not Call List)**: Telemarketers must scrub against the DNCL. AI systems make no difference — the rules apply equally.
- **ADAD (Automatic Dialing-Announcing Device) Rules**: Automated calls must immediately identify the caller and organization, state the purpose, and provide contact information valid for 60 days.
- **Calling Hours**: Weekdays 9:00 AM - 9:30 PM; weekends 10:00 AM - 6:00 PM (local time).
- **Consent**: Can be express or implied, but strict rules govern duration and scope.
- **Penalties**: Up to **$1,000,000 per violation** (individual) or **$10,000,000 per violation** (corporation).

### 3.4 Australia

- **Do Not Call Register Act 2006**: Over 11 million numbers registered. Telemarketers must not call registered numbers without consent.
- **Spam Act 2003**: Primarily governs electronic messages but relevant if calls include recorded content.
- **AI-Specific**: No AI-specific calling law, but the same obligations apply — AI systems must identify themselves immediately and check the DNCR.
- **Privacy Act 1988**: Governs collection and handling of personal information including call recordings.
- **Enforcement**: ACMA (Australian Communications and Media Authority) issues penalties; over **AUD 600,000** in penalties issued in 2023 for non-compliant marketing calls.

---

## 4. Regulatory Trends and Outlook

### Active/Pending Regulatory Actions

1. **FCC NOI on AI in Telecommunications** (Docket 24-220) — may result in new rules specifically targeting AI calling
2. **FTC TSR amendments** — continued tightening of telemarketing rules
3. **State-level AI disclosure laws** — multiple states considering mandatory AI disclosure requirements
4. **EU AI Act enforcement** — phased implementation through 2026

### Key Trends

- **Convergence**: Federal and state regulators are aligning to treat AI voices the same as prerecorded voices
- **Enforcement escalation**: Both the FCC and FTC are increasing enforcement budgets for robocall violations
- **Carrier-level enforcement**: Twilio and other carriers are independently cracking down on spam/robocall traffic, often more aggressively than regulators
- **International harmonization**: Similar approaches emerging globally — consent, disclosure, DNC registers

---

## Sources

- [FCC Makes AI-Generated Voices in Robocalls Illegal](https://www.fcc.gov/document/fcc-makes-ai-generated-voices-robocalls-illegal)
- [FCC 24-17 Full Declaratory Ruling](https://docs.fcc.gov/public/attachments/FCC-24-17A1.pdf)
- [FTC Telemarketing Sales Rule](https://www.ftc.gov/legal-library/browse/rules/telemarketing-sales-rule)
- [FTC March 2024 AI Protections](https://www.ftc.gov/news-events/news/press-releases/2024/03/ftc-implements-new-protections-businesses-against-telemarketing-fraud-affirms-protections-against-ai)
- [FCC TRACED Act Implementation](https://www.fcc.gov/TRACEDAct)
- [FCC Caller ID Spoofing Guide](https://www.fcc.gov/consumers/guides/spoofing)
- [NCLC Top Six TCPA/Robocall Developments 2024/2025](https://library.nclc.org/article/top-six-tcparobocall-developments-20242025)
- [Wiley Alert: FCC AI Voice Restrictions](https://www.wiley.law/alert-FCC-Extends-Regulatory-Reach-Over-AI-Announces-TCPA-Restrictions-Cover-AI-Generated-Voices-in-Outbound-Calls)
- [Henson Legal: TCPA $1,500/Call Fines for AI Platforms](https://www.henson-legal.com/ai-voice-compliance)
- [Justia 50-State Recording Laws Survey](https://www.justia.com/50-state-surveys/recording-phone-calls-and-conversations/)
- [CRTC Telemarketing Rules](https://crtc.gc.ca/eng/phone/telemarketing/reg.htm)
- [Australia DNCR](https://www.donotcall.gov.au/)
