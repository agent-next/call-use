# call-use

## Project
Open-source outbound call-control runtime for AI agents. The "browser-use" for phones.
- **Stack**: LiveKit Agents v1.4 + Deepgram STT + OpenAI GPT-4o + GPT-4o-mini TTS + Twilio SIP
- **Architecture**: FastAPI server (dispatch) + LiveKit agent worker (voice). Communication via LiveKit data channel + room metadata.

## Development

### Setup
```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
make test
```

### Commands
```bash
make test       # Run all tests
make lint       # Run ruff check + format check
make format     # Auto-format code
make build      # Build package
make check      # Full pre-commit check (lint + test + build)
```

### Commit Format
Use conventional commits: `feat(scope):`, `fix(scope):`, `docs:`, `test:`, `ci:`, `chore:`

### Testing
- Write tests first (TDD)
- All tests in `tests/` directory
- Use pytest + pytest-asyncio
- Mock LiveKit imports (see `tests/conftest.py` for patterns)
- Minimum 80% coverage on changed files

### Code Style
- Ruff for linting and formatting
- Line length: 100 characters
- Target: Python 3.11+
- Type hints on all public functions

### Key Technical Notes
- `generate_reply()` MUST be called after `session.start()`, NOT in `on_enter()` (LiveKit issue #2710)
- Agent speech captured via `conversation_item_added` event (not `agent_speech_committed`)
- `call.arguments` is str in livekit-agents v1.4.5, not dict
- `ctx.connect()` IS required with `@server.rtc_session()`
