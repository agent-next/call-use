# SP2: Cloud Backend — Zero-Config Onboarding

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `pip install call-use && call-use dial "+18001234567" -i "Ask hours"` works without ANY infrastructure setup. Three tiers: free sandbox, verified, self-hosted.

**Architecture:** Hosted FastAPI gateway on Fly.io/Railway. Manages LiveKit rooms + Twilio SIP on behalf of users. SDK auto-detects: if local keys exist → self-hosted (Tier 3); if `CALLUSE_API_KEY` → cloud (Tier 1/2). GitHub OAuth for free tier, Twilio Verify for phone binding.

**Tech Stack:** FastAPI, Supabase (auth + DB), Twilio Verify API, Stripe (metered billing), Fly.io (hosting)

---

## File Structure

```
call_use/
├── cloud_client.py      # CREATE — thin HTTP client for call-use cloud API
├── cli.py               # MODIFY — auth command: github login, phone verify, key display
├── sdk.py               # MODIFY — auto-detect cloud vs self-hosted mode

cloud/                   # CREATE — separate deployable, NOT part of pip package
├── app.py               # CREATE — FastAPI cloud gateway
├── auth.py              # CREATE — GitHub OAuth + API key management
├── billing.py           # CREATE — Stripe metered billing
├── phone_verify.py      # CREATE — Twilio Verify for Tier 2
├── rate_limit.py        # CREATE — per-user rate limiting (free: 5/day, paid: usage-based)
├── models.py            # CREATE — User, APIKey, UsageRecord models
├── config.py            # CREATE — env config
├── Dockerfile           # CREATE — container for deployment
├── fly.toml             # CREATE — Fly.io config
└── requirements.txt     # CREATE — cloud-specific deps

tests/
├── test_cloud_client.py # CREATE
├── test_cloud_auth.py   # CREATE
└── test_cloud_app.py    # CREATE
```

---

## Chunk 1: Cloud Gateway API

### Task 1: Cloud data models and config

**Files:**
- Create: `cloud/config.py`
- Create: `cloud/models.py`

- [ ] **Step 1: Write cloud config**

```python
# cloud/config.py
"""Cloud gateway configuration from environment."""
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_VERIFY_SID = os.environ.get("TWILIO_VERIFY_SID", "")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
SIP_TRUNK_ID = os.environ.get("SIP_TRUNK_ID", "")
SANDBOX_CALLER_ID = os.environ.get("SANDBOX_CALLER_ID", "")

# Rate limits
FREE_TIER_DAILY_LIMIT = 5
FREE_TIER_ALLOWED_PREFIXES = ["+1800", "+1888", "+1877", "+1866", "+1855", "+1844", "+1833"]
```

- [ ] **Step 2: Write cloud models**

```python
# cloud/models.py
"""Cloud gateway data models."""
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class UserTier(str, Enum):
    free = "free"       # GitHub OAuth, 800-numbers only, 5/day
    verified = "verified"  # Phone verified, own caller ID, usage-based
    enterprise = "enterprise"  # Custom limits


class CloudUser(BaseModel):
    user_id: str
    github_login: str
    tier: UserTier = UserTier.free
    api_key: str
    verified_phone: str | None = None
    stripe_customer_id: str | None = None
    daily_calls_used: int = 0
    daily_reset_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CloudCallRequest(BaseModel):
    phone: str
    instructions: str
    user_info: dict | None = None
    caller_id: str | None = None  # Tier 2+ only
    voice_id: str | None = None
    timeout: int = 600


class CloudCallResponse(BaseModel):
    task_id: str
    status: str  # "dispatched" | "error"
    monitor_token: str | None = None
    error: str | None = None
```

- [ ] **Step 3: Commit**

```bash
git add cloud/config.py cloud/models.py
git commit -m "feat(cloud): add cloud gateway config and data models"
```

---

### Task 2: Supabase schema and GitHub OAuth authentication

**Files:**
- Create: `cloud/db.py`
- Create: `cloud/auth.py`
- Test: `tests/test_cloud_auth.py`

- [ ] **Step 0: Create Supabase users table and db client**

SQL migration (run via Supabase dashboard or `supabase migration`):

```sql
-- supabase/migrations/001_create_users.sql
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    github_login TEXT UNIQUE NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    api_key TEXT UNIQUE NOT NULL,
    verified_phone TEXT,
    stripe_customer_id TEXT,
    daily_calls_used INTEGER NOT NULL DEFAULT 0,
    daily_reset_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_api_key ON users (api_key);
CREATE INDEX idx_users_github_login ON users (github_login);

-- Atomic rate-limit increment: returns the updated row only if under the limit.
-- If the daily counter belongs to a previous day, reset it first.
CREATE OR REPLACE FUNCTION increment_daily_calls(
    p_user_id TEXT,
    p_limit INTEGER
) RETURNS SETOF users AS $$
BEGIN
    -- Reset counter if it's a new day
    UPDATE users
       SET daily_calls_used = 0,
           daily_reset_at = now()
     WHERE user_id = p_user_id
       AND (daily_reset_at IS NULL OR daily_reset_at::date < now()::date);

    -- Atomically increment only if under limit
    RETURN QUERY
    UPDATE users
       SET daily_calls_used = daily_calls_used + 1
     WHERE user_id = p_user_id
       AND daily_calls_used < p_limit
    RETURNING *;
END;
$$ LANGUAGE plpgsql;
```

```python
# cloud/db.py
"""Supabase client setup."""
from supabase import create_client, Client

from cloud.config import SUPABASE_URL, SUPABASE_KEY


def get_supabase() -> Client:
    """Return a configured Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)
```

- [ ] **Step 1: Write failing test**

```python
# tests/test_cloud_auth.py
"""Tests for cloud auth."""
import pytest
from unittest.mock import patch, AsyncMock

from cloud.auth import create_api_key, validate_api_key


def test_create_api_key_format():
    """API keys have the correct prefix and length."""
    key = create_api_key()
    assert key.startswith("cu_")
    assert len(key) == 35  # cu_ + 32 hex chars


@pytest.mark.asyncio
async def test_validate_api_key_missing():
    """Missing API key returns None."""
    with patch("cloud.auth._get_user_by_key", new_callable=AsyncMock, return_value=None):
        user = await validate_api_key("cu_invalid")
        assert user is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cloud_auth.py -v`
Expected: FAIL

- [ ] **Step 3: Implement auth module**

```python
# cloud/auth.py
"""GitHub OAuth + API key management."""
import secrets
from typing import Optional

import httpx

from cloud.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
from cloud.models import CloudUser, UserTier


def create_api_key() -> str:
    """Generate a new API key."""
    return f"cu_{secrets.token_hex(16)}"


async def github_oauth_callback(code: str) -> CloudUser:
    """Exchange GitHub OAuth code for user profile, create or return user."""
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        access_token = token_data["access_token"]

        # Get user profile
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        github_user = user_resp.json()

    user = await _get_or_create_user(github_user["login"], github_user["id"])
    return user


async def _get_or_create_user(github_login: str, github_id: int) -> CloudUser:
    """Look up or create a user in the database."""
    from cloud.db import get_supabase

    sb = get_supabase()
    # Check if user exists
    result = sb.table("users").select("*").eq("user_id", str(github_id)).execute()
    if result.data:
        return CloudUser(**result.data[0])

    # Create new user
    new_user = {
        "user_id": str(github_id),
        "github_login": github_login,
        "api_key": create_api_key(),
        "tier": "free",
        "daily_calls_used": 0,
    }
    sb.table("users").insert(new_user).execute()
    return CloudUser(**new_user)


async def _get_user_by_key(api_key: str) -> Optional[CloudUser]:
    """Look up user by API key."""
    from cloud.db import get_supabase

    sb = get_supabase()
    result = sb.table("users").select("*").eq("api_key", api_key).execute()
    if result.data:
        return CloudUser(**result.data[0])
    return None


async def validate_api_key(api_key: str) -> Optional[CloudUser]:
    """Validate API key and return user, or None if invalid."""
    if not api_key or not api_key.startswith("cu_"):
        return None
    return await _get_user_by_key(api_key)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_cloud_auth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cloud/auth.py tests/test_cloud_auth.py
git commit -m "feat(cloud): add GitHub OAuth and API key management"
```

---

### Task 3: Rate limiting and abuse prevention

**Files:**
- Create: `cloud/rate_limit.py`

- [ ] **Step 1: Implement per-user rate limiting**

```python
# cloud/rate_limit.py
"""Per-user rate limiting for cloud gateway."""
from cloud.config import FREE_TIER_DAILY_LIMIT, FREE_TIER_ALLOWED_PREFIXES
from cloud.db import get_supabase
from cloud.models import CloudUser, UserTier


class CloudRateLimitError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def check_and_increment_rate_limit(user: CloudUser) -> None:
    """Atomically check and increment the daily call counter in the database.

    Uses the Supabase RPC function `increment_daily_calls` which:
    - Resets the counter if it's a new day
    - Increments only if under the limit
    - Returns 0 rows if the limit is exceeded (atomic — no TOCTOU race)

    Raises CloudRateLimitError if the user has hit their daily limit.
    """
    if user.tier == UserTier.enterprise:
        return  # Enterprise has custom/unlimited limits

    limit = FREE_TIER_DAILY_LIMIT  # Extend per-tier limits as needed

    sb = get_supabase()
    result = sb.rpc("increment_daily_calls", {
        "p_user_id": user.user_id,
        "p_limit": limit,
    }).execute()

    if not result.data:
        raise CloudRateLimitError(
            f"Free tier limit reached ({FREE_TIER_DAILY_LIMIT}/day). "
            "Upgrade with 'call-use auth --phone' or bring your own keys."
        )


def check_phone_allowed(user: CloudUser, phone: str) -> None:
    """Check if user's tier allows calling this number.

    IMPORTANT: Always call validate_phone_number() BEFORE this function
    to ensure the phone string is valid E.164 format. This function only
    checks tier-based prefix restrictions, not format validity.
    """
    if user.tier == UserTier.free:
        allowed = any(phone.startswith(prefix) for prefix in FREE_TIER_ALLOWED_PREFIXES)
        if not allowed:
            raise CloudRateLimitError(
                "Free tier only allows toll-free numbers (800/888/877/866/855/844/833). "
                "Upgrade with 'call-use auth --phone' to call any US number."
            )
```

- [ ] **Step 2: Commit**

```bash
git add cloud/rate_limit.py
git commit -m "feat(cloud): add per-user rate limiting and phone restrictions"
```

---

### Task 4: Phone verification (Tier 2)

**Files:**
- Create: `cloud/phone_verify.py`

- [ ] **Step 1: Implement Twilio Verify integration**

```python
# cloud/phone_verify.py
"""Phone number verification via Twilio Verify for Tier 2 onboarding."""
from twilio.rest import Client

from cloud.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SID


def _get_client() -> Client:
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


async def send_verification(phone: str) -> str:
    """Send SMS verification code. Returns verification SID."""
    client = _get_client()
    verification = client.verify.v2.services(TWILIO_VERIFY_SID).verifications.create(
        to=phone, channel="sms"
    )
    return verification.sid


async def check_verification(phone: str, code: str) -> bool:
    """Check verification code. Returns True if valid."""
    client = _get_client()
    check = client.verify.v2.services(TWILIO_VERIFY_SID).verification_checks.create(
        to=phone, code=code
    )
    return check.status == "approved"
```

- [ ] **Step 2: Commit**

```bash
git add cloud/phone_verify.py
git commit -m "feat(cloud): add Twilio Verify phone verification for Tier 2"
```

---

### Task 5: Cloud FastAPI gateway

**Files:**
- Create: `cloud/app.py`
- Test: `tests/test_cloud_app.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cloud_app.py
"""Tests for cloud gateway API."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from cloud.app import create_cloud_app
from cloud.models import CloudUser, UserTier


@pytest.fixture
def app():
    return create_cloud_app()


@pytest.mark.asyncio
async def test_health_check(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_dial_without_api_key_returns_401(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/calls", json={
            "phone": "+18001234567",
            "instructions": "Ask about hours",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
@patch("cloud.app.validate_api_key", new_callable=AsyncMock)
@patch("cloud.app._dispatch_call", new_callable=AsyncMock)
async def test_dial_free_tier_800_number(mock_dispatch, mock_validate, app):
    mock_validate.return_value = CloudUser(
        user_id="123", github_login="testuser", api_key="cu_test",
        tier=UserTier.free,
    )
    mock_dispatch.return_value = {"task_id": "test-123", "status": "dispatched", "monitor_token": "test-123"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/calls",
            json={"phone": "+18001234567", "instructions": "Ask about hours"},
            headers={"Authorization": "Bearer cu_test"},
        )
        assert resp.status_code == 200
        assert resp.json()["task_id"] == "test-123"


@pytest.mark.asyncio
@patch("cloud.app.validate_api_key", new_callable=AsyncMock)
async def test_dial_free_tier_non_800_rejected(mock_validate, app):
    mock_validate.return_value = CloudUser(
        user_id="123", github_login="testuser", api_key="cu_test",
        tier=UserTier.free,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/calls",
            json={"phone": "+12125551234", "instructions": "test"},
            headers={"Authorization": "Bearer cu_test"},
        )
        assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cloud_app.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cloud gateway**

```python
# cloud/app.py
"""call-use cloud gateway — hosted API for zero-config calling.

Architecture: The gateway NEVER blocks on call completion. It creates a
LiveKit room, dispatches an agent into it, and returns immediately with
a task_id. Clients poll GET /v1/calls/{task_id} for outcome or subscribe
to GET /v1/calls/{task_id}/events (SSE) for real-time updates.

This mirrors the self-hosted server.py pattern which uses fire-and-forget
via agent_dispatch.create_dispatch().
"""
import json
import logging
import os
import uuid
from typing import Optional

import sentry_sdk
from fastapi import FastAPI, HTTPException, Header

from call_use.phone import validate_phone_number
from cloud.auth import validate_api_key, github_oauth_callback
from cloud.config import SANDBOX_CALLER_ID, LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
from cloud.models import CloudCallRequest, CloudCallResponse, CloudUser, UserTier
from cloud.rate_limit import check_and_increment_rate_limit, check_phone_allowed, CloudRateLimitError

logger = logging.getLogger("cloud.app")

# Initialize Sentry for error alerting (reads SENTRY_DSN from env)
sentry_sdk.init(traces_sample_rate=0.1)


def create_cloud_app() -> FastAPI:
    app = FastAPI(
        title="call-use cloud",
        description="Zero-config phone calling for AI agents",
        version="1.0.0",
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/auth/github")
    async def github_auth_start(redirect_port: int | None = None):
        """Redirect to GitHub OAuth.

        If `redirect_port` is provided (from CLI local callback server),
        it's threaded through the GitHub OAuth `state` parameter so the
        callback can redirect the API key back to localhost.
        """
        client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        oauth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=read:user"
        if redirect_port is not None:
            oauth_url += f"&state={redirect_port}"
        return {"url": oauth_url}

    @app.get("/auth/github/callback")
    async def github_auth_callback(code: str, state: str | None = None):
        """Handle GitHub OAuth callback, return API key.

        If `state` contains a port number (passed via GitHub OAuth state
        parameter from /auth/github), redirects to the CLI's local
        callback server instead of displaying JSON in the browser.
        """
        user = await github_oauth_callback(code)

        # If CLI provided a local callback port via OAuth state, redirect the API key there
        if state and state.isdigit():
            from fastapi.responses import RedirectResponse
            return RedirectResponse(
                url=f"http://localhost:{state}/callback?api_key={user.api_key}&tier={user.tier.value}"
            )

        return {
            "api_key": user.api_key,
            "tier": user.tier.value,
            "message": "Save your API key: export CALLUSE_API_KEY='{}'".format(user.api_key),
        }

    @app.post("/v1/calls", response_model=CloudCallResponse)
    async def create_call(
        req: CloudCallRequest,
        authorization: Optional[str] = Header(None),
    ):
        """Create an outbound call via call-use cloud.

        Returns immediately with a task_id. Does NOT block for call duration.
        Use GET /v1/calls/{task_id} to poll for outcome.
        """
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing API key. Run 'call-use auth --github' first.")

        api_key = authorization.replace("Bearer ", "")
        user = await validate_api_key(api_key)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Step 1: Validate phone number format (E.164, 11 digits)
        # This MUST happen before check_phone_allowed() to prevent
        # malformed strings from bypassing prefix checks.
        try:
            validate_phone_number(req.phone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Step 2: Enforce caller_id based on tier (prevent spoofing)
        caller_id = _resolve_caller_id(user, req.caller_id)

        # Step 3: Enforce tier restrictions (phone prefixes)
        try:
            check_phone_allowed(user, req.phone)
        except CloudRateLimitError as e:
            raise HTTPException(status_code=403, detail=e.message)

        # Step 4: Atomic rate limit check + increment in database
        # This is a single DB operation — no in-memory mutation.
        try:
            check_and_increment_rate_limit(user)
        except CloudRateLimitError as e:
            raise HTTPException(status_code=429, detail=e.message)

        # Step 5: Dispatch call (fire-and-forget, returns immediately)
        result = await _dispatch_call(user, req, caller_id)
        logger.info(
            "call_dispatched",
            extra={"call_id": result["task_id"], "user_id": user.user_id, "phone": req.phone},
        )
        return CloudCallResponse(**result)

    @app.get("/v1/calls/{task_id}")
    async def get_call_status(task_id: str, authorization: Optional[str] = Header(None)):
        """Poll for call outcome. Reads status from LiveKit room metadata."""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing API key")

        from livekit import api as lk_proto
        from livekit.api import LiveKitAPI

        async with LiveKitAPI() as lkapi:
            rooms = await lkapi.room.list_rooms(
                lk_proto.ListRoomsRequest(names=[task_id])
            )
            if not rooms.rooms:
                raise HTTPException(status_code=404, detail="Call not found")

            room_data = rooms.rooms[0]
            metadata = json.loads(room_data.metadata) if room_data.metadata else {}
            return {
                "task_id": task_id,
                "status": metadata.get("status", "in_progress"),
                "outcome": metadata.get("outcome"),
            }

    # Optional: SSE endpoint for real-time streaming (future enhancement)
    # @app.get("/v1/calls/{task_id}/events")
    # async def call_events_sse(task_id: str): ...

    return app


def _resolve_caller_id(user: CloudUser, requested_caller_id: str | None) -> str | None:
    """Resolve caller_id based on user tier. Prevents caller ID spoofing.

    - free tier: ALWAYS use SANDBOX_CALLER_ID, ignore any request
    - verified tier: ONLY allow user's own verified_phone
    - enterprise tier: allow any validated caller_id
    """
    if user.tier == UserTier.free:
        return SANDBOX_CALLER_ID
    elif user.tier == UserTier.verified:
        # Verified users can only use their own verified phone
        return user.verified_phone
    else:  # enterprise
        return requested_caller_id


async def _dispatch_call(user: CloudUser, req: CloudCallRequest, caller_id: str | None) -> dict:
    """Dispatch a call via LiveKit agent — fire-and-forget.

    Creates a LiveKit room and dispatches the call-use agent into it,
    then returns immediately. This mirrors the self-hosted server.py
    pattern (lkapi.agent_dispatch.create_dispatch()) and does NOT block
    for the call duration (which can be up to 600 seconds).

    The agent writes its outcome to the room metadata, which can be
    polled via GET /v1/calls/{task_id}.
    """
    from livekit import api as lk_proto
    from livekit.api import LiveKitAPI

    task_id = f"cu-{uuid.uuid4().hex[:12]}"

    async with LiveKitAPI() as lkapi:
        # Fire-and-forget: dispatch agent into room, return immediately.
        # sip_trunk_id is NOT passed here — it's configured in the
        # LiveKit SIP trunk setup, not per-call.
        await lkapi.agent_dispatch.create_dispatch(
            lk_proto.CreateAgentDispatchRequest(
                agent_name="call-use-agent",
                room=task_id,
                metadata=json.dumps({
                    "phone_number": req.phone,
                    "caller_id": caller_id,
                    "instructions": req.instructions,
                    "user_info": req.user_info or {},
                    "voice_id": req.voice_id,
                    "timeout_seconds": req.timeout,
                }),
            )
        )

    logger.info(
        "agent_dispatched",
        extra={"call_id": task_id, "user_id": user.user_id},
    )

    return {
        "task_id": task_id,
        "status": "dispatched",
        "monitor_token": task_id,  # Can be used to poll /v1/calls/{task_id}
    }
```

> **Note on cost tracking:** Each call incurs costs across multiple providers:
> Twilio (SIP trunk minutes), LiveKit (media server), OpenAI (LLM tokens),
> and Deepgram (STT minutes). Structured logging with `call_id` and `user_id`
> on every log line enables per-call cost attribution. Integrate with a billing
> pipeline that reads these structured logs to compute per-user costs.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_cloud_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cloud/app.py tests/test_cloud_app.py
git commit -m "feat(cloud): add FastAPI cloud gateway with tier enforcement"
```

---

## Chunk 2: SDK Cloud Auto-Detection

### Task 6: Cloud client for SDK

**Files:**
- Create: `call_use/cloud_client.py`
- Modify: `call_use/cli.py`

- [ ] **Step 1: Implement cloud client**

```python
# call_use/cloud_client.py
"""Thin HTTP client for call-use cloud API."""
import json
import os
import webbrowser

import httpx

CLOUD_API_URL = os.environ.get("CALLUSE_API_URL", "https://api.calluse.dev")


def get_api_key() -> str | None:
    """Get cloud API key from environment."""
    return os.environ.get("CALLUSE_API_KEY")


def is_cloud_mode() -> bool:
    """True if using cloud backend (no local LiveKit keys, has cloud key)."""
    has_local = all(os.environ.get(k) for k in ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"])
    has_cloud = get_api_key() is not None
    return has_cloud and not has_local


async def cloud_dial(
    phone: str,
    instructions: str,
    user_info: dict | None = None,
    caller_id: str | None = None,
    voice_id: str | None = None,
    timeout: int = 600,
) -> dict:
    """Make a call via cloud API."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "No API key. Run 'call-use auth --github' for free tier, "
            "or set LIVEKIT_URL/LIVEKIT_API_KEY/LIVEKIT_API_SECRET for self-hosted."
        )

    async with httpx.AsyncClient(timeout=timeout + 30) as client:
        resp = await client.post(
            f"{CLOUD_API_URL}/v1/calls",
            json={
                "phone": phone,
                "instructions": instructions,
                "user_info": user_info,
                "caller_id": caller_id,
                "voice_id": voice_id,
                "timeout": timeout,
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code == 401:
            raise RuntimeError("Invalid API key. Run 'call-use auth --github' to get a new one.")
        if resp.status_code == 403:
            raise RuntimeError(resp.json().get("detail", "Rate limited"))
        resp.raise_for_status()
        return resp.json()


def start_github_auth() -> str:
    """Run GitHub OAuth flow with a local callback server.

    1. Start a temporary HTTP server on a random port
    2. Open browser to GitHub OAuth with redirect_uri pointing to localhost
    3. After auth, the cloud server redirects back to localhost with the API key
    4. CLI captures the key, saves to config, and stops the server
    5. Fallback: if browser can't open, show URL for manual flow
    """
    import json
    import socket
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from pathlib import Path
    from urllib.parse import urlparse, parse_qs

    # Find a free port
    with socket.socket() as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    captured_key: dict = {}
    server_ready = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if "api_key" in params:
                captured_key["api_key"] = params["api_key"][0]
                captured_key["tier"] = params.get("tier", ["free"])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authenticated!</h1><p>You can close this tab.</p>")
            else:
                self.send_response(400)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress server logs

    server = HTTPServer(("127.0.0.1", port), CallbackHandler)
    server.timeout = 120  # 2 minute timeout

    # The cloud server's /auth/github/callback will redirect to localhost:{port}
    auth_url = f"{CLOUD_API_URL}/auth/github?redirect_port={port}"

    try:
        webbrowser.open(auth_url)
    except Exception:
        print(f"Could not open browser. Visit this URL manually:\n  {auth_url}")
        print("Then paste your API key below:")
        manual_key = input("API key: ").strip()
        if manual_key:
            _save_api_key(manual_key)
            return f"API key saved. Run: export CALLUSE_API_KEY='{manual_key}'"
        return "Authentication cancelled."

    # Wait for callback — loop to handle spurious requests (e.g. /favicon.ico)
    import time
    deadline = time.time() + 120
    while not captured_key and time.time() < deadline:
        server.handle_request()
    server.server_close()

    if "api_key" in captured_key:
        _save_api_key(captured_key["api_key"])
        return f"Authenticated as {captured_key['tier']} tier. API key saved to ~/.config/call-use/config.json"
    return "Authentication timed out. Try again with 'call-use auth --github'."


def _save_api_key(api_key: str) -> None:
    """Save API key to config file."""
    import json
    from pathlib import Path

    config_dir = Path.home() / ".config" / "call-use"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"

    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text())
    config["api_key"] = api_key
    config_file.write_text(json.dumps(config, indent=2))
```

- [ ] **Step 2: Update CLI dial to auto-detect cloud mode**

In `call_use/cli.py`, modify `_run_call()`:

```python
def _run_call(
    phone: str,
    instructions: str,
    user_info: dict | None = None,
    caller_id: str | None = None,
    voice_id: str | None = None,
    timeout: int = 600,
    approval_required: bool = False,
) -> dict:
    """Run a call. Auto-detects cloud vs self-hosted mode."""
    from call_use.cloud_client import is_cloud_mode

    if is_cloud_mode():
        from call_use.cloud_client import cloud_dial
        return asyncio.run(cloud_dial(
            phone=phone,
            instructions=instructions,
            user_info=user_info,
            caller_id=caller_id,
            voice_id=voice_id,
            timeout=timeout,
        ))

    from call_use.sdk import CallAgent
    agent = CallAgent(
        phone=phone,
        instructions=instructions,
        user_info=user_info,
        caller_id=caller_id,
        voice_id=voice_id,
        approval_required=approval_required,
        timeout_seconds=timeout,
        on_event=_event_printer,
    )
    outcome = asyncio.run(agent.call())
    return outcome.model_dump(mode="json")
```

- [ ] **Step 3: Update CLI auth command to use cloud client**

Replace the auth command stub with working GitHub flow:

```python
@main.command()
@click.option("--github", is_flag=True, help="Authenticate via GitHub OAuth (free tier).")
@click.option("--phone", "phone_number", default=None, help="Verify phone number via SMS (paid tier).")
def auth(github, phone_number):
    """Authenticate with call-use cloud for zero-config calling."""
    from call_use.cloud_client import start_github_auth, CLOUD_API_URL

    if github:
        msg = start_github_auth()
        click.echo(msg, err=True)
        return

    if phone_number:
        click.echo(f"Phone verification: coming in next release.", err=True)
        click.echo("For now, use --github for free tier.", err=True)
        return

    click.echo("Run 'call-use auth --github' for free tier (5 calls/day to 800 numbers).", err=True)
```

- [ ] **Step 4: Commit**

```bash
git add call_use/cloud_client.py call_use/cli.py
git commit -m "feat(cloud): add cloud client with auto-detection in CLI"
```

---

### Task 7: Deployment config

**Files:**
- Create: `cloud/Dockerfile`
- Create: `cloud/fly.toml`
- Create: `cloud/requirements.txt`

- [ ] **Step 1: Write Dockerfile** (see updated Dockerfile in Step 3 below)

- [ ] **Step 2: Write fly.toml**

```toml
# cloud/fly.toml
app = "call-use-cloud"
primary_region = "iad"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[env]
  CALLUSE_ENV = "production"
```

- [ ] **Step 3: Write requirements**

```
# cloud/requirements.txt
fastapi>=0.100
uvicorn
httpx
twilio
stripe
supabase
sentry-sdk[fastapi]
# call-use is installed via COPY + pip install in the Dockerfile (local source).
# For production after PyPI publication, use: call-use>=1.0.0
```

Update the Dockerfile to install call-use from local source instead of git:

```dockerfile
# cloud/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install cloud dependencies first (layer caching)
COPY cloud/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install call-use from local source (pinned to this build, not git HEAD)
COPY pyproject.toml setup.cfg ./
COPY call_use/ /app/call_use/
RUN pip install --no-cache-dir .

COPY cloud/ /app/cloud/

EXPOSE 8080
CMD ["uvicorn", "cloud.app:create_cloud_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
```

- [ ] **Step 4: Commit**

```bash
git add cloud/Dockerfile cloud/fly.toml cloud/requirements.txt
git commit -m "feat(cloud): add deployment config for Fly.io"
```

---

## Summary

| Task | Description | Tier |
|------|-------------|------|
| 1 | Cloud config + models | All |
| 2 | Supabase schema + GitHub OAuth auth + db client | Tier 1 |
| 3 | Rate limiting (atomic DB ops) + phone restrictions | Tier 1 |
| 4 | Twilio Verify phone binding | Tier 2 |
| 5 | Cloud FastAPI gateway (async dispatch, caller ID enforcement, phone validation) | All |
| 6 | SDK cloud auto-detection + local OAuth callback server | All |
| 7 | Deployment config (local COPY install, Sentry) | Ops |

**Total: 7 tasks, ~10 commits, ~600 lines of new code**

---

## Review Findings Applied

This plan incorporates fixes for the following review findings:

1. **CRITICAL: Async dispatch** — `_dispatch_call()` uses fire-and-forget via `create_dispatch()` (mirrors `server.py`). Added `GET /v1/calls/{task_id}` polling endpoint.
2. **CRITICAL: Atomic rate limits** — `check_and_increment_rate_limit()` uses a Supabase RPC function. No in-memory mutation.
3. **CRITICAL: Phone validation** — `validate_phone_number()` called before `check_phone_allowed()` in `create_call`.
4. **HIGH: OAuth key delivery** — CLI starts a local HTTP server; cloud redirects API key to `localhost:{port}/callback`.
5. **HIGH: Caller ID spoofing** — `_resolve_caller_id()` enforces per-tier rules (free=sandbox, verified=own phone, enterprise=any).
6. **HIGH: Prefix bypass** — Validation chain is: `validate_phone_number()` (format) → `check_phone_allowed()` (tier prefix).
7. **MEDIUM: `datetime.utcnow()` deprecated** — Replaced with `datetime.now(timezone.utc)`.
8. **MEDIUM: Supabase stubs** — Task 2 now includes SQL schema, `cloud/db.py`, and real Supabase queries in auth.py.
9. **MEDIUM: No observability** — Added `sentry-sdk`, structured logging with `call_id`/`user_id`, cost tracking note.
10. **MEDIUM: Unpinned git dep** — Dockerfile uses `COPY + pip install .` from local source. Requirements note for PyPI after publication.

### Round 2 Findings

11. **HIGH: OAuth `redirect_port` lost** — `/auth/github` now accepts `redirect_port` query param and threads it through GitHub OAuth `state` parameter. `/auth/github/callback` reads `state` to get the port and redirects API key to `localhost:{state}`.
12. **CRITICAL: `call_use.agent_dispatch` does not exist** — `_dispatch_call` now uses the LiveKit API directly (`lkapi.agent_dispatch.create_dispatch` with `CreateAgentDispatchRequest`), matching the pattern in `sdk.py` and `server.py`. Removed `sip_trunk_id` from dispatch (configured in SIP trunk setup, not per-call).
13. **MEDIUM: OAuth callback server single-shot** — `handle_request()` now loops with a 120s deadline until `captured_key` is populated, preventing `/favicon.ico` from consuming the only request.
14. **LOW: Test mock missing `monitor_token`** — Added `"monitor_token": "test-123"` to `mock_dispatch.return_value` to match `CloudCallResponse` model.
