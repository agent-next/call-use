# Security Audit Report — call-use v0.1.0

**Audit Date**: 2026-03-14
**Auditor**: Automated static analysis of all Python source files in `call_use/`
**Scope**: `call_use/agent.py`, `call_use/server.py`, `call_use/sdk.py`, `call_use/mcp_server.py`, `call_use/cli.py`, `call_use/evidence.py`, `call_use/phone.py`, `call_use/rate_limit.py`, `call_use/models.py`

---

## Summary

call-use is an outbound voice-call agent runtime using LiveKit, Deepgram, and OpenAI. The codebase is well-structured and avoids the most severe categories of vulnerability (no `eval`/`exec`, no shell injection, no SQL injection). However, several meaningful security issues were identified spanning authentication, input validation, PII logging, concurrency, and operational hardening. No critical vulnerabilities were found; the highest severity finding is HIGH.

**Overall Risk Level: MEDIUM** — Safe for controlled/internal deployment; requires remediation before general public or production release.

---

## Findings

---

### [HIGH] Timing-oracle API key comparison in server.py

- **File**: `call_use/server.py:69`
- **Description**: The API key is compared using the `!=` operator (`if x_api_key != api_key`), which is a standard string comparison subject to timing side-channels. An attacker who can make many precisely-timed requests could, in theory, infer the key byte-by-byte.
- **Impact**: In environments where network jitter is low (same datacenter), this could be exploited to brute-force or confirm API key candidates. The risk is real for low-entropy keys.
- **Recommendation**: Replace with `hmac.compare_digest(x_api_key, api_key)` (constant-time comparison). Also enforce a minimum key entropy requirement (32+ random bytes or characters, not human-chosen passwords).

```python
import hmac
if not hmac.compare_digest(x_api_key, api_key):
    raise HTTPException(401, "Invalid API key")
```

---

### [HIGH] `task_id` / room name generated with `random`, not `secrets`

- **File**: `call_use/server.py:120`
- **Description**: The `task_id` (which doubles as the LiveKit room name) is generated using `random.choices(string.ascii_lowercase, k=8)`. Python's `random` module uses a Mersenne Twister PRNG that is **not** cryptographically secure. With 8 lowercase characters, the keyspace is only 26^8 ≈ 208 billion — small enough to enumerate with GPU hardware. The room name is a bearer credential: anyone who guesses it can join the LiveKit room as a monitor participant.
- **Impact**: An attacker who can observe even a single `task_id` value (e.g., from a leaked response body or log) can seed the PRNG and predict future room names, gaining access to live calls.
- **Recommendation**: Use `secrets.token_hex(16)` (128-bit cryptographic randomness) for task/room IDs in `server.py`. The `models.py` `_generate_task_id` and `mcp_server.py` already use `uuid4` (which is cryptographically secure on all major platforms), so only `server.py` needs fixing.

```python
import secrets
task_id = "call-" + secrets.token_hex(8)
```

---

### [HIGH] No input size limits on `instructions`, `user_info`, or `message` fields

- **File**: `call_use/server.py:21-27`, `call_use/server.py:189`, `call_use/mcp_server.py:127-133`
- **Description**: The `instructions` (str), `user_info` (dict), `recording_disclaimer` (str), and the `message` field in `/inject` are accepted without any size constraints. A caller can submit megabyte-sized payloads, which will be: (a) forwarded verbatim into LiveKit room metadata (which has its own size limits but the error is unhandled cleanly), (b) injected into LLM context (inflating token cost and potentially causing prompt injection), and (c) written to disk in the evidence log.
- **Impact**: Denial-of-service via inflated token costs; potential OOM in metadata handling; amplified prompt-injection attack surface.
- **Recommendation**: Add Pydantic field validators with maximum lengths. Suggested limits:
  - `instructions`: max 4000 characters
  - `recording_disclaimer`: max 500 characters
  - `user_info`: max 50 keys, values max 500 chars each
  - `message` in `/inject`: max 2000 characters
  - `timeout_seconds`: clamp to `[30, 3600]`

---

### [HIGH] MCP `dial` tool skips phone number validation

- **File**: `call_use/mcp_server.py:35-88`, specifically `_do_dial`
- **Description**: The `mcp_server.py` `_do_dial` function dispatches a call using the `phone` parameter directly in metadata without calling `validate_phone_number()`. By contrast, `server.py` and `sdk.py` both call the validator. This means an AI agent using the MCP interface can submit arbitrary strings as phone numbers (e.g., premium-rate numbers, non-E.164 strings, or empty strings) and they will be passed to the SIP trunk without validation.
- **Impact**: Premium-rate fraud (900/976 numbers), international dialing (non-NANP numbers if the SIP trunk allows them), unexpected SIP behavior from malformed numbers.
- **Recommendation**: Add validation in `_do_dial`:

```python
from call_use.phone import validate_phone_number, validate_caller_id
phone = validate_phone_number(phone)
if caller_id:
    caller_id = validate_caller_id(caller_id)
```

---

### [HIGH] `voice_id` is not validated before being passed to OpenAI TTS

- **File**: `call_use/agent.py:543`
- **Description**: `tts_voice = task.voice_id or "alloy"` — the `voice_id` field from user input is passed directly to `openai.TTS(voice=tts_voice)` without validating it against the allowed set (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`). An arbitrary string is forwarded to the OpenAI API.
- **Impact**: An attacker who can influence the `voice_id` field can probe the OpenAI TTS API with arbitrary values. While this is unlikely to cause data exfiltration, it can cause unexpected errors or, in future OpenAI API versions, potentially trigger different behaviors.
- **Recommendation**: Validate `voice_id` against an allowlist in `CreateCallRequest` (Pydantic `Literal` type) and/or in `_build_instructions`:

```python
from typing import Literal
ALLOWED_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
voice_id: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] | None = None
```

---

### [MEDIUM] PII (phone numbers, transcripts) written to local log files without access controls

- **File**: `call_use/evidence.py:18,104-125`
- **Description**: `EvidencePipeline.finalize()` writes a JSON log file containing the full call transcript, phone number, caller ID, and all call events to `~/.call-use/logs/<task_id>.json`. The directory is created with `mkdir(parents=True, exist_ok=True)` using default umask permissions (typically `0o755` on Linux, readable by all users on the system). The transcript includes verbatim speech from both parties.
- **Impact**: Any local user on a multi-tenant system (e.g., shared cloud VM, CI runner) can read the complete call transcripts and phone numbers of all calls processed by this agent.
- **Recommendation**: Create the log directory with restrictive permissions (`0o700`) and log files with `0o600`:

```python
LOGS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
log_path = LOGS_DIR / f"{self.task.task_id}.json"
log_path.touch(mode=0o600)
with open(log_path, "w") as f:
    ...
```

---

### [MEDIUM] Error messages from phone validation exposed verbatim in HTTP 400 responses

- **File**: `call_use/server.py:110,118`
- **Description**: `raise HTTPException(400, str(e))` exposes the full `ValueError` message from `validate_phone_number`, which includes the literal phone number: e.g., `"Invalid phone number '+19001234567': must be E.164 NANP format"`. While this is not catastrophic (the caller already knows the number), it reflects a pattern of leaking internal validation details.
- **Impact**: Low direct impact, but establishes a pattern of leaking internal state in error messages. If similar patterns are copied to more sensitive validators, it could leak sensitive data.
- **Recommendation**: Use generic error messages in HTTP responses and log the specific detail server-side:

```python
except ValueError as e:
    logger.debug("Phone validation failed: %s", e)
    raise HTTPException(400, "Invalid phone_number or caller_id format")
```

---

### [MEDIUM] Takeover token uses static identity "supervisor"

- **File**: `call_use/server.py:238`
- **Description**: Every takeover token is issued with `with_identity("supervisor")`. If two calls are taken over simultaneously, the second takeover token will collide with the first in the LiveKit room (identity must be unique per room). More importantly, if the supervisor's session from a previous call lingers (e.g., slow disconnect), a new takeover on a different call won't be able to join because the identity is already in use in that room. This is also a minor authorization concern: the token grants room-scoped permissions but the identity `"supervisor"` provides no call-level traceability.
- **Impact**: Operational disruption in concurrent takeover scenarios; lack of audit trail for which human supervised which call.
- **Recommendation**: Use a unique identity per takeover: `f"supervisor-{task_id[:8]}"`.

---

### [MEDIUM] Rate limiter is per-API-key, in-memory, and not shared across workers

- **File**: `call_use/rate_limit.py`, `call_use/server.py:58-61`
- **Description**: The `RateLimiter` is a pure in-memory data structure scoped to a single process. When deployed with multiple uvicorn workers (`--workers N`), each worker maintains its own rate limit counter. A client can make up to `max_calls * N` requests per window by distributing requests across workers. Additionally, the rate limiter state is lost on every process restart.
- **Impact**: Rate limits can be bypassed by factor of N workers; no persistence across restarts.
- **Recommendation**: Document this limitation prominently. For production, use a shared store (Redis with sliding window via `ZRANGEBYSCORE`). At minimum, document that the server must run with a single worker or behind a rate-limiting proxy (nginx, cloud load balancer).

---

### [MEDIUM] No CORS configuration — FastAPI defaults to no CORS, but no explicit deny

- **File**: `call_use/server.py:49`
- **Description**: The FastAPI app is created without any CORS middleware. FastAPI's default behavior is to not add CORS headers, which means browsers will block cross-origin requests (safe by default). However, this is undocumented and an operator adding `CORSMiddleware` with `allow_origins=["*"]` (a common mistake when debugging) would open the API to CSRF-like attacks from any browser.
- **Impact**: Low current risk, but the lack of explicit CORS policy is a governance gap.
- **Recommendation**: Add explicit CORS middleware in `create_app` with a restrictive default (`allow_origins=[]`) and document that operators should set an allowlist for any web frontend integrations.

---

### [MEDIUM] `_get_call_lock` creates locks on first access — not thread-safe without GIL guarantee

- **File**: `call_use/server.py:63-66`
- **Description**: `_get_call_lock` creates a new `asyncio.Lock` if one doesn't exist for a `call_id`. Because this function is not itself protected by a lock, there's a theoretical TOCTOU window: two concurrent requests for the same new `call_id` could both observe `call_id not in _call_locks` and create separate lock objects. The asyncio GIL and single event loop make this extremely unlikely in practice, but it's not guaranteed if uvicorn ever runs multiple event loops.
- **Impact**: Very low probability; in the unlikely case both requests create separate locks, the serialization guarantee of `_get_call_lock` is silently broken, allowing two concurrent state-modifying operations on the same call.
- **Recommendation**: Use `setdefault` for atomic insertion:

```python
def _get_call_lock(call_id: str) -> asyncio.Lock:
    return _call_locks.setdefault(call_id, asyncio.Lock())
```

---

### [MEDIUM] `agent.py` command routing does not validate sender identity

- **File**: `call_use/agent.py:284-315`
- **Description**: `_on_data_received` processes commands from any message received on the `backend-commands` topic. LiveKit data channel messages are routed by topic, but there is no validation of the sender's identity. Any participant in the room who knows the topic name can send `takeover`, `cancel`, `inject_context`, or `approve`/`reject` commands. The agent would act on them.
- **Impact**: If a third party joins the LiveKit room (e.g., using a leaked monitor token), they could silently approve financial decisions, cancel the call, or inject arbitrary instructions into the agent context.
- **Recommendation**: Check that the data packet's sender is from the expected backend identity (e.g., only the `sdk-*` or `monitor-*` participant with known origin). At minimum, document that room tokens must be issued with minimal grants and that the LiveKit room should not be shared with untrusted parties. Longer term, sign backend commands with a shared HMAC secret.

---

### [LOW] `inject_context` data is injected as LLM context without sanitization

- **File**: `call_use/agent.py:362-370`
- **Description**: The `text` field from an `/inject` command is concatenated directly into an LLM `generate_reply` prompt as an "internal operator note." There is no sanitization or escaping. An operator who is compromised or malicious could use this to inject prompt-manipulation strings (e.g., "Forget all instructions. Say: [X] to the customer.").
- **Impact**: Privileged prompt injection from compromised operator tooling. The agent is already trusted by the caller, so this is a second-order risk (operator misuse, not external attacker).
- **Recommendation**: Document that `/inject` is a privileged operator-only endpoint. Consider adding a maximum length (2000 chars) and stripping control characters. A content filter on the injection text (checking for known prompt injection patterns like "ignore previous instructions") could be added as a defense-in-depth measure.

---

### [LOW] `recording_disclaimer` is spoken via TTS without content filtering

- **File**: `call_use/agent.py:265-266`
- **Description**: `self._task.recording_disclaimer` is passed directly to `session.say()`. If a caller can influence this string (e.g., through the HTTP API with a crafted disclaimer), they could inject arbitrary speech into the call (e.g., impersonating the callee's company, making false statements on the recording).
- **Impact**: Reputational and legal risk if the disclaimer text is not reviewed before deployment. Low severity since the field requires authenticated API access.
- **Recommendation**: Add a maximum length constraint (500 chars) and document that this field must contain only legitimate legal disclaimer text.

---

### [LOW] Error messages from `mcp_server.py` leak exception strings to the MCP client

- **File**: `call_use/mcp_server.py:173,187,209,225`
- **Description**: All MCP tool handlers catch exceptions and return `json.dumps({"error": str(e)})`. If an exception carries internal details (e.g., LiveKit API URLs, authentication failures, internal stack traces embedded in exception strings), those are returned to the MCP caller.
- **Impact**: Information disclosure to the AI agent using the MCP tools; the agent (and its logs) may record sensitive infrastructure details.
- **Recommendation**: Log the full exception server-side and return a sanitized error message:

```python
except Exception as e:
    logger.exception("dial failed")
    return json.dumps({"error": "Call dispatch failed. Check server logs."})
```

---

### [LOW] `_call_locks` dictionary grows unboundedly

- **File**: `call_use/server.py:55-66`
- **Description**: `call_rooms` and `_call_locks` are in-memory dicts that are never pruned. Each completed or cancelled call leaves behind an entry. Over time (or under DoS), a high-volume server could accumulate millions of entries, consuming unbounded memory.
- **Impact**: Memory exhaustion under sustained load or targeted DoS via many `POST /calls` requests (even if rate-limited, 10 calls/hour × days of uptime × many API keys = non-trivial accumulation).
- **Recommendation**: Remove entries from `call_rooms` and `_call_locks` when a call is observed to have ended (e.g., when `GET /calls/{call_id}` returns `state: ended`, or via a cleanup background task).

---

### [LOW] `timeout_seconds` has no upper bound validation

- **File**: `call_use/server.py:26`, `call_use/mcp_server.py:132`
- **Description**: `timeout_seconds: int = 600` is accepted from user input without a maximum value. A caller could set `timeout_seconds=86400` (24 hours), causing the agent to keep a SIP call alive for a day, accruing substantial telephony costs.
- **Impact**: Financial abuse via runaway call duration.
- **Recommendation**: Clamp to a maximum (e.g., `Field(default=600, ge=30, le=3600)`) in the Pydantic model.

---

### [LOW] `caller_id` ownership not verified

- **File**: `call_use/phone.py:110` (TODO comment), `call_use/server.py:113-118`
- **Description**: The code includes a self-acknowledged `# TODO v2: Verify caller_id ownership via Twilio Lookup API`. Any authenticated caller can spoof any US phone number as their caller ID. This is a standard telephony limitation but worth noting explicitly.
- **Impact**: Caller ID spoofing; potential abuse for fraudulent calls (robocall compliance, STIR/SHAKEN violations).
- **Recommendation**: Document this limitation clearly in the public README and SECURITY.md. Prioritize Twilio Lookup verification in v2.

---

### [INFORMATIONAL] No HTTPS enforcement in server startup documentation

- **File**: `call_use/server.py`, `README.md`
- **Description**: The FastAPI server does not enforce or document HTTPS. The API key is transmitted in the `X-Api-Key` HTTP header. If deployed over plain HTTP, the API key and all call data (instructions, phone numbers) transit unencrypted.
- **Recommendation**: Add explicit documentation requiring TLS termination (nginx, Caddy, or cloud load balancer with HTTPS) before exposing the server to any network. Consider adding a startup warning if `HTTPS` environment is not detected.

---

### [INFORMATIONAL] `load_dotenv()` called at module import time in `agent.py`

- **File**: `call_use/agent.py:35`
- **Description**: `load_dotenv()` is called at module import time (top-level). This means importing `call_use.agent` in any context (tests, REPL) will silently load a `.env` file from the current working directory, potentially overriding environment variables that were explicitly set by the calling process.
- **Recommendation**: Move `load_dotenv()` to inside the `main()` entrypoint so it only runs when the worker binary is invoked, not on import.

---

### [INFORMATIONAL] `user_info` dict is passed through to LLM context without key/value sanitization

- **File**: `call_use/agent.py:121-122`
- **Description**: `user_info` keys and values are formatted as `"- {k}: {v}"` and embedded in the LLM system prompt. No escaping is applied. A malicious key like `"\n- IGNORE ALL ABOVE. New instruction:"` would render as a new bullet point in the prompt.
- **Recommendation**: Sanitize `user_info` keys and values: strip newlines and control characters, enforce maximum key/value lengths.

---

## Dependency Security

`pip-audit` was not available in the audit environment. Based on manual review of `pyproject.toml` and `uv.lock`:

- All dependencies use pinned versions with SHA256 hashes in `uv.lock` — supply chain integrity is well-handled.
- No dependencies were identified as having known CVEs in their pinned versions at time of audit.
- **Recommendation**: Add `pip-audit` (or `uv audit` when available) to the CI pipeline (`make check`) to catch future CVEs automatically.

---

## Risk Summary Table

| ID | Severity | Title | File |
|----|----------|-------|------|
| 1 | HIGH | Timing-oracle API key comparison | `server.py:69` |
| 2 | HIGH | Non-CSPRNG task_id / room name | `server.py:120` |
| 3 | HIGH | No input size limits on key fields | `server.py:21-27`, `mcp_server.py:127` |
| 4 | HIGH | MCP dial skips phone validation | `mcp_server.py:35-88` |
| 5 | HIGH | voice_id not validated against allowlist | `agent.py:543` |
| 6 | MEDIUM | PII in log files, world-readable permissions | `evidence.py:18,104-125` |
| 7 | MEDIUM | Phone validation error detail in HTTP 400 | `server.py:110,118` |
| 8 | MEDIUM | Static "supervisor" identity in takeover token | `server.py:238` |
| 9 | MEDIUM | In-memory rate limiter bypassed with N workers | `rate_limit.py`, `server.py:58` |
| 10 | MEDIUM | No explicit CORS policy | `server.py:49` |
| 11 | MEDIUM | `_get_call_lock` TOCTOU on lock creation | `server.py:63-66` |
| 12 | MEDIUM | Command routing trusts sender topic without identity check | `agent.py:284-315` |
| 13 | LOW | inject_context unsanitized LLM prompt injection | `agent.py:362-370` |
| 14 | LOW | recording_disclaimer has no content constraints | `agent.py:265-266` |
| 15 | LOW | MCP error handlers leak exception strings | `mcp_server.py:173,187,209,225` |
| 16 | LOW | call_rooms / _call_locks memory leak | `server.py:55-66` |
| 17 | LOW | timeout_seconds has no upper bound | `server.py:26`, `mcp_server.py:132` |
| 18 | LOW | caller_id ownership not verified | `phone.py:110` |
| 19 | INFO | No HTTPS enforcement documented | `server.py` |
| 20 | INFO | load_dotenv() at module import time | `agent.py:35` |
| 21 | INFO | user_info keys/values not sanitized in LLM prompt | `agent.py:121-122` |

---

## Prioritized Remediation Order

**Before public release (must fix):**
1. Finding 4 — MCP phone number validation (trivial fix, high impact)
2. Finding 2 — CSPRNG for task IDs (`secrets.token_hex`)
3. Finding 1 — Timing-safe API key comparison (`hmac.compare_digest`)
4. Finding 3 — Input size limits (Pydantic field constraints)
5. Finding 5 — voice_id allowlist validation
6. Finding 6 — Log file permissions (`0o700`/`0o600`)

**Before production deployment (should fix):**
7. Finding 12 — Sender identity validation on data channel commands
8. Finding 9 — Document rate limiter multi-worker limitation
9. Finding 8 — Per-call-unique takeover identity
10. Finding 17 — timeout_seconds upper bound
11. Finding 16 — call_rooms/call_locks cleanup

**Hardening (nice to have):**
12. Findings 13, 14, 21 — Input sanitization for LLM-injected fields
13. Finding 15 — Sanitize MCP error messages
14. Finding 20 — Move load_dotenv() to entrypoint only
