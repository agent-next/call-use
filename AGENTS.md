# call-use — agent guide

Org rules: https://github.com/agent-next/.github/blob/main/AGENT-STANDARD.md (hard limits, PR/merge policy).

## Purpose

Open-source outbound call-control runtime: lets AI agents dial real phones,
navigate IVR menus, talk to humans, and return structured outcomes (Python SDK
`call_use/sdk.py`, CLI `call_use/cli.py`, MCP server `call_use/mcp_server.py`,
REST API `call_use/server.py`). Status: beta (v0.1). Docs site config:
`mkdocs.yml` + `docs/`; release notes in `CHANGELOG.md`.

## Orient

`git status`, `git branch --show-current`, `git worktree list`,
`gh pr list --state open`. Read first: `README.md`, `CONTRIBUTING.md`,
`pyproject.toml`, `Makefile`. Public repo — check open PRs before touching
shared files like `Makefile` or `README.md`.

## Setup

`make setup` creates `.venv/` when no virtualenv is active (the Makefile
prepends `.venv/bin` to PATH, so host/conda Python is never touched), then runs
`python3 -m pip install -e ".[dev]" ruff build twine` — the package editable
with dev extras plus the lint/build tools `make check` needs that live outside
the `dev` extra. Requires Python >= 3.11.

## Check

`make check` = `lint` (ruff check + ruff format --check) + `typecheck` (mypy) +
`test` (pytest with `--cov-fail-under=100`) + `build` (`python3 -m build` +
`twine check`) — the same gates CI runs in `.github/workflows/ci.yml` (CI adds
separate security/commit-lint/pr-size jobs). Narrow variants: `make test-unit`,
`make test-bdd`, `make test-integration`, `make lint`, `make typecheck`.
Tests are hermetic: LiveKit/plugins are stubbed in `tests/conftest.py`, no
network or credentials needed.

## Boundaries

- Public repo — never commit secrets; credentials are referenced by env-var
  NAME only (see `.env.example`: LIVEKIT_*, SIP_TRUNK_ID, DEEPGRAM_API_KEY,
  OPENAI_API_KEY, API_KEY).
- Real calls spend real money (Twilio/LiveKit/OpenAI/Deepgram). Do not run the
  agent, examples, or `web/` demo against live credentials.
- Coverage is CI-enforced at 100% — new code needs tests or the `test` job
  fails.
- Do not edit `.github/workflows/` in baseline/style PRs; CI is stable.

## Done

Branch per change -> PR; a test with a real oracle for new code; `make check`
green; CI green before merge; receipts (commands + output) in the PR body.
Conventional-commit messages (`feat(agent): ...`) — CI runs commitizen on PRs.
