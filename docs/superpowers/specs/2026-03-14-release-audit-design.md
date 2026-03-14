# call-use v0.1.0 Release Audit Design

## Goal

Bring call-use to a mature, stable state for its first public release. Address all gaps found in the pre-release audit across governance, code quality, safety, testing, and documentation.

## Phases

Each phase is an independent PR, merged sequentially.

### Phase 1: Governance & Infrastructure

**Scope**: Project tooling, CI, and contributor experience.

| Item | What | Why |
|------|------|-----|
| CLAUDE.md | Create with coding standards, test requirements, commit format | No AI coding guidelines exist |
| Makefile | `test`, `lint`, `format`, `typecheck` targets | No standardized dev commands |
| .pre-commit-config.yaml | ruff check + ruff format hooks | No pre-commit enforcement |
| CI type-checking | Add mypy step to ci.yml | No static type analysis in CI |
| CI coverage | Add pytest-cov, report coverage, set ≥80% gate | Coverage unknown |
| CONTRIBUTING.md | Branch naming, PR flow, local dev guide, code style | Current version is 3 lines |

**Acceptance**: `make test`, `make lint`, `make typecheck` all pass. CI runs all steps. Pre-commit hooks catch formatting issues.

### Phase 2: Code Quality & Safety

**Scope**: Code fixes, security documentation, test infrastructure.

| Item | What | Why |
|------|------|-----|
| Remove `_lk_utils.py` | Delete empty placeholder file | Dead code in release |
| Handle `auth` CLI stub | Remove `auth` subcommand entirely; document as future feature in README | "Coming soon" in a released CLI is confusing |
| SIP error classification | Replace string matching in `agent.py:563-570` with enum-based classification using `SipEndReason` constants | Fragile string matching on Twilio error text |
| In-memory state docs | Add "Limitations" section to README noting `call_rooms` is in-memory, lost on restart | Users need to know this |
| SECURITY.md update | Add caller ID ownership gap disclosure | Known security consideration not documented |
| Shared test fixtures | Extract LiveKit mock setup from 3 test files into `conftest.py` | Duplicated ~50 lines across test_agent.py, test_sdk.py, test_server.py |

**Acceptance**: All tests pass. No empty files shipped. CLI has no stub commands. SIP errors use typed constants.

### Phase 3: Test Coverage & Documentation

**Scope**: Missing tests, coverage enforcement, docs consistency.

| Item | What | Why |
|------|------|-----|
| SDK async path tests | Test `CallAgent.call()`, `takeover()`, `resume()` execution paths | Only constructor validation tested currently |
| Coverage config | pytest-cov in pyproject.toml, ≥80% on `call_use/` | No measurement exists |
| CHANGELOG.md | Expand with detailed feature list for v0.1.0 | Single-line entry insufficient for release |
| README consistency | Verify all code examples, env vars, CLI flags match actual code | Pre-release doc check |

**Acceptance**: `pytest --cov=call_use --cov-fail-under=80` passes. CHANGELOG is comprehensive. README examples are accurate.

## Out of Scope

- New features (approval flow v2, persistence layer, auth command implementation)
- Performance optimization
- LiveKit/Twilio version upgrades
- Integration tests against real LiveKit instances

## Risk

- Type-checking may surface issues in LiveKit plugin type stubs — may need `type: ignore` for third-party code
- Coverage gate may require additional tests beyond what's planned — adjust threshold if needed
