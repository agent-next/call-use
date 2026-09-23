# call-use Compliance Guide

> Last updated: 2026-03-14

Practical compliance guide for call-use users making automated outbound phone calls with AI agents. This guide covers US federal and state law. Users operating in other jurisdictions must consult local regulations.

**Disclaimer**: This guide is informational only and does not constitute legal advice. Consult a licensed attorney for specific compliance questions.

---

## 1. What Users MUST Do

### 1.1 Obtain Prior Express Consent

**Federal law (TCPA + FCC 2024 Ruling) requires consent before making AI voice calls.**

| Call Type | Consent Required | Standard |
|-----------|-----------------|----------|
| Marketing/sales to residential lines | Prior Express Written Consent (PEWC) | Signed written agreement (electronic ok) |
| Marketing/sales to cell phones | Prior Express Written Consent (PEWC) | Signed written agreement (electronic ok) |
| Informational to residential lines | Prior Express Consent | Verbal or written, documented |
| Informational to cell phones | Prior Express Consent | Verbal or written, documented |
| Emergency/healthcare notifications | Varies | May be exempt, consult counsel |

**What constitutes valid written consent:**
- A clear and conspicuous written disclosure that the person will receive automated/AI-generated calls
- The person's signature (electronic signatures valid under E-SIGN Act)
- Consent must be **voluntary** — cannot be a condition of purchase
- Must identify the specific caller/entity authorized to call
- Must identify the phone number(s) to be called

**Record retention**: Maintain proof of consent for a minimum of **5 years**.

### 1.2 Honor Do Not Call Requests

- Maintain an **internal Do Not Call list** of all persons who have asked not to be called
- Process opt-out requests within **10 business days** (as of April 2025)
- For telemarketing: subscribe to the **National Do Not Call Registry** and scrub call lists at least every **31 days**
- Never call a number that has been added to your internal DNC list, regardless of prior consent

### 1.3 Identify the Caller at the Start of Every Call

Within the first few seconds of every call, the AI agent must:

1. State the **name of the individual or company** on whose behalf the call is being made
2. Disclose that the caller is an **AI agent** (required by FCC 2024 ruling and various state laws)
3. State the **purpose** of the call

**Example opening:**
> "Hello, this is an AI assistant calling on behalf of [Company Name]. I'm calling about [purpose]. This call may be recorded. Would you like to continue?"

### 1.4 Provide an Opt-Out Mechanism

Every call must provide a way for the recipient to:
- Request to be placed on the Do Not Call list
- End the call immediately
- For prerecorded portions: provide an automated opt-out mechanism (e.g., "Press 2 to be removed from our call list")

### 1.5 Maintain Call Records

Maintain the following records for a minimum of **5 years** (TSR requirement for telemarketing) or **4 years** (TCPA statute of limitations):

- Date, time, and duration of each call
- Phone number called
- Caller ID displayed
- Purpose/category of call
- Consent documentation for the called number
- Opt-out requests received
- Call recordings (if applicable, subject to recording consent laws)

### 1.6 Comply with Recording Consent Laws

If call-use is configured to record calls or generate transcripts:

**In two-party consent states (CA, CT, DE, FL, IL, MD, MA, MI, MT, NV, NH, PA, WA):**
- The AI agent **must** inform the called party that the call is being recorded **before** any recording begins
- The called party must **consent** (continuing the call after notification may constitute implied consent in some states, but explicit consent is safer)

**In one-party consent states (all others):**
- Recording is permitted if one party (the caller/user) consents
- Best practice: disclose recording anyway

**Interstate calls:**
- Apply the **stricter** standard — if either party is in a two-party consent state, follow two-party rules
- When in doubt, always disclose recording

**Recording disclaimer template:**
> "This call is being recorded for quality assurance and record-keeping purposes. Do you consent to continue?"

### 1.7 Display Accurate Caller ID

- Display a valid phone number that can receive calls (Truth in Caller ID Act)
- The displayed number must accurately represent the calling party
- Never display a number you do not own or are not authorized to use
- Twilio requires number verification, but users must not circumvent these controls

### 1.8 Respect Calling Hours

- **Federal**: Do not call before **8:00 AM** or after **9:00 PM** in the **called party's local time zone**
- **Some states have stricter windows** — check state-specific rules
- **Canada**: Weekdays 9:00 AM - 9:30 PM; weekends 10:00 AM - 6:00 PM

---

## 2. What Users MUST NOT Do

### 2.1 Do Not Call Numbers on the National DNC Registry (Without Consent)

- If engaging in telemarketing, you **must** check the DNC Registry
- Exception: You may call DNC-registered numbers if you have **prior express written consent** or an **established business relationship** (within 18 months of last transaction or 3 months of last inquiry)

### 2.2 Do Not Spoof Caller ID for Deceptive Purposes

- Transmitting misleading caller ID with intent to defraud or cause harm violates the **Truth in Caller ID Act**
- Penalties: Up to **$10,000 per violation**
- Displaying your business number (instead of a personal number) is permitted and encouraged

### 2.3 Do Not Call Before 8 AM or After 9 PM Local Time

- This is the called party's time zone, not yours
- Implement timezone detection based on the area code or user-provided data
- call-use users should configure calling windows in their application logic

### 2.4 Do Not Use AI Voices Without Disclosure

- Per the **FCC February 2024 ruling**, AI-generated voices are "artificial" under the TCPA
- **You must disclose that the caller is an AI** at the beginning of the call
- Failure to disclose AI use may constitute a separate violation
- California imposes **$500 fines per undisclosed AI interaction** (SB 1001)

### 2.5 Do Not Abandon Calls

- TSR limits call abandonment to **3% per campaign per 30-day period**
- If a call connects but no agent (human or AI) is available, it counts as abandoned
- Abandoned calls must play a prerecorded message with opt-out information

### 2.6 Do Not Ignore State-Specific Requirements

- Many states have their own telemarketing registration requirements
- Some states require posting a surety bond
- Research the specific requirements for every state where you make calls

---

## 3. Best Practices

### 3.1 Consent Collection Best Practices

**Web form consent example:**

```
[ ] I consent to receive automated phone calls from [Company Name]
    at the phone number provided above, including calls made using
    AI-generated voice technology. I understand these calls may be
    recorded. I can revoke consent at any time by [method].

    Message and data rates may apply. Consent is not a condition
    of purchase.
```

**Key elements:**
- Separate checkbox (not bundled with other consents)
- Names the specific company
- Mentions AI/automated nature
- Mentions recording
- Explains revocation method
- Not a condition of purchase

### 3.2 Recording Disclaimer Templates

**Standard (recommended for all calls):**
> "Hello, this is an AI assistant calling on behalf of [Company Name]. This call may be recorded for quality and compliance purposes. If you do not wish to be recorded, please let me know now."

**Two-party consent state version:**
> "Hello, this is an AI assistant calling on behalf of [Company Name]. This call will be recorded. Do you consent to the recording? If not, I can continue without recording."

**Minimal (one-party consent states only):**
> "Hello, this is an AI assistant calling on behalf of [Company Name]. This call may be monitored or recorded."

### 3.3 Record Retention Requirements

| Record Type | Retention Period | Legal Basis |
|-------------|-----------------|-------------|
| Consent documentation | 5 years minimum | TSR Section 310.5(a) |
| Call logs (date, time, number, duration) | 5 years minimum | TSR Section 310.5(a) |
| DNC requests | Indefinite (or duration of business + 5 years) | TCPA, TSR |
| Call recordings | Per business need, minimum 2 years recommended | Best practice |
| Marketing materials/scripts | 5 years | TSR Section 310.5(a) |
| AI voice configurations | Duration of use + 2 years | Best practice (FTC recordkeeping) |

### 3.4 Opt-Out Implementation

**During the call:**
- The AI agent should respond to any opt-out request immediately (e.g., "Please stop calling," "Remove me," "Do not call")
- Confirm the opt-out: "I've noted your request. You will not receive further calls from us."
- Log the opt-out request with timestamp

**After the call:**
- Add the number to your internal DNC list within **10 business days** (preferably immediately)
- Remove from all future call campaigns
- Send confirmation if contact information is available

**Technical implementation recommendations:**
- Implement keyword detection for opt-out phrases ("stop," "remove," "do not call," "unsubscribe")
- Maintain a centralized DNC database that all calling campaigns check before dialing
- Implement automated DNC Registry scrubbing on a 31-day cycle

### 3.5 AI Disclosure Best Practices

- Disclose AI nature in the **first sentence** of the call
- Use clear language: "AI assistant," "automated system," "virtual agent"
- Do **not** attempt to pass the AI off as human
- If asked "Are you a robot/AI?", always answer **truthfully**
- Consider offering transfer to a human agent

### 3.6 Pre-Call Checklist

Before initiating any call campaign with call-use:

- [ ] Verified consent documentation exists for all numbers
- [ ] Scrubbed against National DNC Registry (within last 31 days)
- [ ] Scrubbed against internal DNC list
- [ ] Calling hours configured for recipient time zones
- [ ] AI disclosure included in opening script
- [ ] Recording disclaimer included (if recording)
- [ ] Opt-out mechanism configured
- [ ] Caller ID displays valid, owned number
- [ ] Call logs being captured
- [ ] State-specific requirements checked for all target states

---

## 4. Penalties Summary

| Violation | Penalty | Enforced By |
|-----------|---------|-------------|
| TCPA violation (per call) | $500 - $1,500 | Private lawsuits, FCC, State AGs |
| TSR violation | $50,120 per violation | FTC |
| DNC Registry violation | $50,120 per violation | FTC |
| Caller ID spoofing | $10,000 per violation (max $1M) | FCC |
| State recording violation (CA) | $5,000 per violation + criminal | State courts, DA |
| State recording violation (FL) | Third-degree felony | State courts |
| AI disclosure violation (CA SB 1001) | $500 per interaction | State AG |

---

## Sources

- [FCC TCPA Rules](https://www.fcc.gov/document/fcc-confirms-tcpa-applies-ai-technologies-generate-human-voices)
- [FTC Telemarketing Compliance Guide](https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule)
- [National Do Not Call Registry](https://www.ftc.gov/terms/do-not-call)
- [TCPA Consent Requirements](https://secureprivacy.ai/blog/telephone-consumer-protection-act-compliance-tcpa-2025-full-guide)
- [TCPA Opt-Out Rules (April 2025)](https://www.bclplaw.com/en-US/events-insights-news/the-tcpas-new-opt-out-rules-take-effect-on-april-11-2025-what-does-this-mean-for-businesses.html)
- [Justia 50-State Recording Laws](https://www.justia.com/50-state-surveys/recording-phone-calls-and-conversations/)
