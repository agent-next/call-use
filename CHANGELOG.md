# Changelog

## [0.1.0] - 2026-03-14

### Added
- Python SDK: `CallAgent` class for programmatic outbound calls
- CLI: `call-use dial` command for agent-native phone calls
- MCP Server: 4 async tools (`dial`, `status`, `cancel`, `result`) for Claude Code / Codex
- REST API: `create_app()` for multi-tenant deployments (9 endpoints)
- LiveKit-based voice agent with GPT-4o + Deepgram STT + OpenAI TTS
- Approval flow: agent pauses for human approval on sensitive actions
- Human takeover: pause agent mid-call, take over the conversation
- Phone validation: E.164 NANP format, blocks premium/Caribbean numbers
- JSON audit logs per call
- Agent skill: `skill.md` for Claude Code and compatible agent frameworks
- Framework examples: LangChain, OpenAI Agents SDK, Claude Code MCP setup
