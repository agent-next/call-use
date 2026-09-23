# call-use v0.1.2 — Engineering Plan Review

**Date:** 2026-03-16
**Mode:** BIG CHANGE
**Status:** Review complete, all decisions resolved

---

## Decisions Made

| # | Issue | Decision |
|---|---|---|
| 1 | Factory location | A) In agent.py — ~30-line factory function co-located with usage |
| 2 | Provider transport to worker | B) Pass in task metadata JSON, fallback to env var |
| 3 | DRY env var mappings | B) Shared constants module imported by all 4 entry points |
| 4 | Google plugin dependency | A) Hard dependency — `livekit-plugins-google~=1.4` |
| 5 | `_get_agent_identity` duplication | A) Extract to shared module |
| T1 | Model selection per provider | A) Add to TODOS.md (P2, depends on PR #66) |
| T2 | Swappable STT provider | A) Add to TODOS.md (P3, depends on PR #66) |

---

## Architecture

### Provider Pipeline Selection (embed in agent.py near factory)

```
  CALL_USE_LLM_PROVIDER (from metadata, fallback env)
         │
         ├── "openai" ──────► STT: deepgram │ LLM: openai │ TTS: openai
         ├── "google" ──────► STT: deepgram │ LLM: google │ TTS: google
         ├── "openrouter" ──► STT: deepgram │ LLM: openai(base_url=OR) │ TTS: openai
         ├── "grok" ────────► STT: deepgram │ LLM: openai(base_url=xAI) │ TTS: openai
         └── unknown ───────► ConfigurationError
```

### TTS Strategy (Approach B — confirmed)
- OpenAI: own TTS (`openai.TTS`)
- Google: own TTS (`google.TTS`)
- OpenRouter: OpenAI TTS fallback (needs `OPENAI_API_KEY`)
- Grok: OpenAI TTS fallback (needs `OPENAI_API_KEY`)

### Data Flow: Provider Selection

```
  User sets CALL_USE_LLM_PROVIDER env var
         │
         ▼
  CLI/SDK/MCP validates env vars for that provider
         │
         ▼
  SDK/MCP includes "provider" in task metadata JSON
         │
         ▼
  LiveKit dispatches agent with metadata
         │
         ▼
  agent.py entrypoint() reads provider from metadata
  (fallback: reads CALL_USE_LLM_PROVIDER from env)
         │
         ▼
  _create_pipeline(provider, voice) returns (STT, LLM, TTS)
         │
         ▼
  AgentSession created with correct plugins
```

---

## Implementation Plan (all via worktree + PR)

### PR #66: Provider Refactor
Branch: `fix/provider-refactor`

**Changes:**
1. Create `call_use/_shared.py` (or `_constants.py`):
   - `PROVIDER_ENV_VARS` dict (extracted from cli.py:21-32)
   - `VALID_VOICES` frozenset (deduplicated from 3 locations)
   - `get_agent_identity()` function (deduplicated from sdk.py + mcp_server.py)
   - `BASE_ENV_VARS` dict

2. `agent.py`:
   - Add `_create_pipeline(provider: str, voice: str)` factory (~30 lines)
   - Read provider from task metadata in `entrypoint()` (fallback to env)
   - Add `from livekit.plugins import google` import
   - Embed ASCII diagram of provider pipeline in code comment

3. `sdk.py`:
   - Make `required_vars` in `call()` provider-aware (import from shared)
   - Add `provider` to task metadata JSON
   - Import `get_agent_identity` from shared instead of local copy

4. `mcp_server.py`:
   - Make `required` in `_do_dial()` provider-aware (import from shared)
   - Add `provider` to task metadata JSON
   - Import `get_agent_identity` from shared instead of local copy
   - Import `VALID_VOICES` from shared

5. `cli.py`:
   - Import `_PROVIDER_ENV_VARS` from shared (remove local copy)

6. `pyproject.toml`:
   - Add `livekit-plugins-google~=1.4` to dependencies

**Tests (same PR):**
- 4 unit tests: factory returns correct plugins per provider
- 1 test: unknown provider → ConfigurationError
- 1 test: grok without XAI_API_KEY → ConfigurationError
- 1 test: openrouter without OPENAI_API_KEY → ConfigurationError
- 4 tests: _check_env per provider (update existing)
- 2 tests: doctor command with non-OpenAI providers
- 1 test: provider in metadata overrides env var
- 1 test: missing provider in metadata falls back to env

**Files touched:** agent.py, sdk.py, mcp_server.py, cli.py, pyproject.toml, + _shared.py (new)
**Test files touched:** test_agent.py, test_cli.py, test_sdk.py, test_mcp_server.py

### PR #67: Simulator Mode
Scope undefined — needs clarification before implementation.

### PR #68: README Rewrite
Docs-only PR. Update provider documentation, add Google/OpenRouter/Grok examples.

### PR #69: MCP Approval Fix
Scope undefined — needs clarification.

### PR #70: Changelog + Version Bump
Mechanical. Depends on all above.

---

## Failure Modes

| Codepath | Failure Mode | Test? | Error Handling? | Silent? |
|---|---|---|---|---|
| Factory: unknown provider | Unrecognized string | NO → add | NO → add | **CRITICAL GAP** |
| Factory: grok no XAI key | Missing env var | NO → add | NO → add | **CRITICAL GAP** |
| Factory: google import | Plugin not installed | NO → add | ImportError | NO |
| SDK env mismatch | SDK validates openai, worker uses grok | NO → add | Metadata fixes | NO |
| OpenRouter API down | base_url unreachable | NO | Plugin timeout | NO |
| Metadata: no provider | Key missing from JSON | NO → add | Fallback to env | NO |

---

## NOT in Scope

1. PR #67 (simulator mode) — scope undefined
2. PR #69 (MCP approval fix) — scope undefined
3. Inbound call support — v0.2
4. STT provider swapping — TODOS.md P3
5. Model selection per provider — TODOS.md P2

## What Already Exists

| Sub-problem | Existing Code | Reused? |
|---|---|---|
| Provider env var mapping | cli.py:21-32 | YES — extract to shared |
| Provider selection UI | cli.py:282-349 (setup wizard) | YES — unchanged |
| Env var validation | cli.py:42-50 (_check_env) | YES — refactor |
| Phone validation | phone.py | YES — unchanged |
| Task metadata pipeline | sdk.py → LiveKit → agent.py | YES — add provider field |
| _get_agent_identity() | sdk.py:31 + mcp_server.py:256 | YES — deduplicate |

## TODOS.md Items

1. **Model selection per provider** — P2, S effort, depends on PR #66
2. **Swappable STT provider** — P3, S effort, depends on PR #66
