# Contributing to call-use

## Quick Start

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
make test
```

## Development Workflow

1. Create a branch: `git checkout -b feat/your-feature` or `fix/your-bug`
2. Write tests first
3. Implement your changes
4. Run `make check` (lint + test + build)
5. Commit with conventional format: `feat(agent): add new greeting mode`
6. Open a PR against `main`

## Branch Naming

- `feat/` — new features
- `fix/` — bug fixes
- `docs/` — documentation only
- `refactor/` — code changes that don't add features or fix bugs

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Run `make format` to auto-format
- Line length: 100 characters
- Type hints on all public functions

## Testing

- Tests go in `tests/`
- Use pytest + pytest-asyncio
- LiveKit is mocked in tests (see `tests/conftest.py`)
- Run `make test` to verify

## Architecture

See the [README](README.md#architecture) for an overview. Key files:

| File | Purpose |
|------|---------|
| `call_use/agent.py` | LiveKit voice agent (state machine + conversation) |
| `call_use/sdk.py` | Public `CallAgent` SDK class |
| `call_use/server.py` | FastAPI REST API |
| `call_use/cli.py` | CLI (`call-use dial`) |
| `call_use/mcp_server.py` | MCP server for Claude Code |
| `call_use/models.py` | Pydantic data models |
| `call_use/evidence.py` | Transcript + event collection |
| `call_use/phone.py` | Phone number validation |
