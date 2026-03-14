# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Email the maintainers or use [GitHub Security Advisories](https://github.com/agent-next/call-use/security/advisories/new)
3. Include steps to reproduce and potential impact

We will respond within 48 hours and work with you on a fix.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Security Considerations

- **Phone numbers**: call-use validates and blocks premium-rate (900/976) and Caribbean numbers
- **API keys**: Never commit `.env` files. Use `.env.example` as a template
- **Call recordings**: Transcripts may contain PII. Handle logs in `~/.call-use/logs/` accordingly
- **SIP trunk**: Secure your Twilio SIP trunk credentials
- **Caller ID**: v0.1 only validates caller ID format (E.164). It does NOT verify ownership. Spoofing is possible. Caller ID verification (via Twilio Lookup API) is planned for v0.2.
