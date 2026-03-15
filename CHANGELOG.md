# Changelog

All notable changes to call-use will be documented in this file.

## [0.1.1] — 2026-03-15

### Changed
- Rewrote README for clarity and impact
- Reduced external project references
- Fixed hardcoded version in tests

### Security
- 5 HIGH-severity security fixes (timing-safe API key comparison, cryptographic task IDs, input validation limits, MCP phone validation, voice_id allowlist)
- Added legal notice to README

## [0.1.0] — 2026-03-14

### Added
- **Python SDK** (`CallAgent`): async outbound call control with event streaming
- **REST API** (FastAPI): 8 endpoints for call lifecycle management with API key auth
- **CLI** (`call-use dial`): make calls from the terminal with real-time transcript streaming
- **MCP Server**: 4 tools (dial, status, cancel, result) for Claude Code / AI agent integration
- **IVR navigation**: DTMF tone generation, voicemail detection, hold/transfer handling
- **Human takeover**: pause the AI agent, join the call, hand back control
- **Approval flow**: agent pauses for human sign-off before sensitive actions
- **Evidence pipeline**: structured transcript + event logs to `~/.call-use/logs/`
- **Phone validation**: E.164 NANP format, premium-rate number blocking, Caribbean NPA blocking
- **Rate limiting**: sliding-window per-API-key rate limiter for the REST API

### Security
- Premium-rate (900/976) and Caribbean number blocking
- API key authentication for REST endpoints
- Caller ID format validation (ownership verification planned for v0.2)
