# Contributing

Thank you for your interest in contributing to call-use.

## Quick start

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
make test
```

## Development workflow

1. **Create a branch**: `git checkout -b feat/your-feature` or `fix/your-bug`
2. **Write tests first** (TDD)
3. **Implement your changes**
4. **Run `make check`** (lint + typecheck + test + build)
5. **Commit with conventional format**: `feat(agent): add new greeting mode`
6. **Open a PR** against `main`

## Branch naming

| Prefix | Purpose |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `refactor/` | Code changes that don't add features or fix bugs |

## Code style

- **Formatter/linter**: [ruff](https://docs.astral.sh/ruff/)
- **Line length**: 100 characters
- **Target**: Python 3.11+
- **Type hints**: Required on all public functions
- **Auto-format**: `make format`
- **Check style**: `make lint`

## Testing

- Tests go in `tests/`
- Use pytest + pytest-asyncio
- LiveKit is mocked in tests (see `tests/conftest.py` for patterns)
- Run with: `make test`
- Coverage target: 100% line coverage

## Project structure

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
| `call_use/rate_limit.py` | Sliding-window rate limiter |

## Make targets

| Target | Command |
|--------|---------|
| `make test` | Run all tests with coverage |
| `make lint` | Check code style |
| `make format` | Auto-format code |
| `make typecheck` | Run mypy type checking |
| `make build` | Build distribution packages |
| `make check` | Full pre-commit check (lint + typecheck + test + build) |
| `make clean` | Remove build artifacts |

## Commit messages

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat(agent): add voicemail detection
fix(sdk): handle timeout correctly
docs: update installation guide
test(cli): add approval flow tests
refactor(models): simplify enum naming
```

## Opening a PR

1. Ensure all checks pass: `make check`
2. Write a clear PR description explaining what and why
3. Link any related issues
4. Keep PRs focused -- one feature or fix per PR
