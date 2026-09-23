# call-use Legal Disclaimer

> Last updated: 2026-03-14

Draft text for inclusion in the call-use README, documentation, and repository.

---

## README Legal Notice (Primary — Add to README.md)

```markdown
## Legal Notice

call-use is a developer tool for legitimate business communication automation.
**Users are solely responsible for complying with all applicable laws and
regulations when using this software.**

### Key Legal Requirements

By using call-use, you acknowledge and agree that:

- **Consent Required**: The FCC's February 2024 ruling classifies AI-generated
  voices as "artificial" under the Telephone Consumer Protection Act (TCPA).
  You **must** obtain prior express consent before making automated calls, and
  prior express **written** consent for marketing calls. Violations carry
  penalties of **$500-$1,500 per call**.

- **Do Not Call Compliance**: If making telemarketing calls, you must comply
  with the National Do Not Call Registry and honor all opt-out requests within
  10 business days.

- **AI Disclosure**: You **must** disclose that the caller is an AI at the
  beginning of every call. Multiple federal and state laws require this
  disclosure.

- **Caller ID**: You must display accurate caller ID information. Spoofing
  caller ID with intent to defraud is a federal crime with fines up to
  $10,000 per violation.

- **Recording Consent**: If recording calls, you must comply with applicable
  state recording consent laws. Thirteen US states require **all-party consent**
  (California, Connecticut, Delaware, Florida, Illinois, Maryland,
  Massachusetts, Michigan, Montana, Nevada, New Hampshire, Pennsylvania,
  Washington).

- **Calling Hours**: Do not call before 8:00 AM or after 9:00 PM in the
  recipient's local time zone.

This software is provided "AS IS" without warranty of any kind. The authors
and contributors are not liable for any legal consequences arising from the
use of this software. This notice does not constitute legal advice — consult
a qualified attorney for compliance guidance specific to your use case.

See [Legal Compliance Guide](docs/legal/compliance-guide.md) for detailed
requirements.
```

---

## Short Disclaimer (For Docs Pages, API Reference, etc.)

```markdown
> **Legal**: call-use users are solely responsible for complying with the TCPA,
> FTC Telemarketing Sales Rule, state recording consent laws, and all other
> applicable regulations. AI-generated voice calls require prior express consent
> under FCC rules (February 2024). See our
> [Legal Compliance Guide](docs/legal/compliance-guide.md) for details.
```

---

## Installation/Setup Disclaimer (Display During First Run or Setup)

```
==========================================================================
                         LEGAL NOTICE
==========================================================================

call-use enables AI agents to make automated phone calls. You are solely
responsible for using this tool in compliance with all applicable laws,
including but not limited to:

  * TCPA (Telephone Consumer Protection Act) — consent required for AI calls
  * FTC Telemarketing Sales Rule — Do Not Call Registry compliance
  * FCC regulations — AI voice disclosure required (Feb 2024 ruling)
  * State laws — recording consent, telemarketing registration
  * Truth in Caller ID Act — accurate caller ID required

Misuse of this tool for spam, fraud, harassment, or unsolicited robocalls
is prohibited and may result in civil and criminal penalties.

By continuing, you acknowledge these legal obligations.
==========================================================================
```

---

## Contributing/Developer Disclaimer (For CONTRIBUTING.md)

```markdown
## Legal Responsibility

call-use is designed for legitimate business automation. When contributing:

- Do not add features whose primary purpose is to circumvent consent
  requirements, spoof caller ID, or evade Do Not Call lists.
- Default configurations should include AI disclosure and recording consent
  prompts.
- Any feature that could be used to deceive call recipients about the AI
  nature of the caller should be documented with appropriate warnings.
```

---

## Hosted Service Disclaimer (For Landing Page / Sign-Up Flow)

```markdown
### Terms of Use

By creating a call-use account, you agree to our [Terms of Service](/legal/tos)
and [Acceptable Use Policy](/legal/aup), and you certify that:

1. You will obtain proper consent before all automated calls
2. You will comply with the TCPA, FTC rules, and all applicable state laws
3. You will disclose the AI nature of calls to all recipients
4. You will honor all Do Not Call and opt-out requests
5. You will display accurate caller ID information
6. You will comply with applicable call recording consent laws
7. You will not use the service for spam, fraud, harassment, or impersonation

Violation of these terms will result in immediate account termination.
```

---

## License File Addendum (Optional — Add After MIT License Text)

```markdown
## Additional Notice

While this software is licensed under the MIT License, its use is subject to
applicable telecommunications regulations including the Telephone Consumer
Protection Act (TCPA), FCC rules on AI-generated voice calls, the FTC
Telemarketing Sales Rule, state telemarketing and recording consent laws,
and the Truth in Caller ID Act. The MIT License does not exempt users from
compliance with these laws.
```

---

## Usage Notes

1. The **README Legal Notice** is the most important — it should be prominently placed in the README, ideally near the top or in a dedicated section that is not easily missed.

2. The **Installation Disclaimer** should be displayed during `npm install`, first CLI run, or initial setup wizard.

3. The **Hosted Service Disclaimer** requires checkbox acknowledgment before account activation, with the timestamp and text version stored.

4. All disclaimers should be reviewed by legal counsel before publication.

5. Update the compliance guide link paths to match the actual documentation structure.
