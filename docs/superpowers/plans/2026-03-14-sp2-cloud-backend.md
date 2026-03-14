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
from datetime import datetime
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
    created_at: datetime = Field(default_factory=datetime.utcnow)


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

### Task 2: GitHub OAuth authentication

**Files:**
- Create: `cloud/auth.py`
- Test: `tests/test_cloud_auth.py`

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
    # TODO: Replace with Supabase lookup
    user = CloudUser(
        user_id=str(github_id),
        github_login=github_login,
        api_key=create_api_key(),
    )
    return user


async def _get_user_by_key(api_key: str) -> Optional[CloudUser]:
    """Look up user by API key."""
    # TODO: Replace with Supabase lookup
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
from datetime import datetime, timezone

from cloud.config import FREE_TIER_DAILY_LIMIT, FREE_TIER_ALLOWED_PREFIXES
from cloud.models import CloudUser, UserTier


class CloudRateLimitError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def check_rate_limit(user: CloudUser) -> None:
    """Check if user can make another call. Raises CloudRateLimitError if not."""
    now = datetime.now(timezone.utc)

    # Reset daily counter if new day
    if user.daily_reset_at is None or now.date() > user.daily_reset_at.date():
        user.daily_calls_used = 0
        user.daily_reset_at = now

    if user.tier == UserTier.free:
        if user.daily_calls_used >= FREE_TIER_DAILY_LIMIT:
            raise CloudRateLimitError(
                f"Free tier limit reached ({FREE_TIER_DAILY_LIMIT}/day). "
                "Upgrade with 'call-use auth --phone' or bring your own keys."
            )


def check_phone_allowed(user: CloudUser, phone: str) -> None:
    """Check if user's tier allows calling this number."""
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
    mock_dispatch.return_value = {"task_id": "test-123", "status": "dispatched"}

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
"""call-use cloud gateway — hosted API for zero-config calling."""
import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header

from cloud.auth import validate_api_key, github_oauth_callback
from cloud.models import CloudCallRequest, CloudCallResponse, CloudUser
from cloud.rate_limit import check_rate_limit, check_phone_allowed, CloudRateLimitError


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
    async def github_auth_start():
        """Redirect to GitHub OAuth."""
        client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        return {"url": f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=read:user"}

    @app.get("/auth/github/callback")
    async def github_auth_callback(code: str):
        """Handle GitHub OAuth callback, return API key."""
        user = await github_oauth_callback(code)
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
        """Create an outbound call via call-use cloud."""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing API key. Run 'call-use auth --github' first.")

        api_key = authorization.replace("Bearer ", "")
        user = await validate_api_key(api_key)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Enforce tier restrictions
        try:
            check_rate_limit(user)
            check_phone_allowed(user, req.phone)
        except CloudRateLimitError as e:
            raise HTTPException(status_code=403, detail=e.message)

        # Use verified phone as caller_id for Tier 2+
        caller_id = req.caller_id
        if user.verified_phone and not caller_id:
            caller_id = user.verified_phone

        result = await _dispatch_call(user, req, caller_id)
        user.daily_calls_used += 1
        return CloudCallResponse(**result)

    return app


async def _dispatch_call(user: CloudUser, req: CloudCallRequest, caller_id: str | None) -> dict:
    """Dispatch a call via LiveKit agent."""
    from call_use.sdk import CallAgent

    agent = CallAgent(
        phone=req.phone,
        instructions=req.instructions,
        user_info=req.user_info,
        caller_id=caller_id,
        voice_id=req.voice_id,
        approval_required=False,
        timeout_seconds=req.timeout,
    )
    outcome = await agent.call()
    return {
        "task_id": outcome.task_id,
        "status": "dispatched",
        "monitor_token": None,
    }
```

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


def start_github_auth():
    """Open browser for GitHub OAuth, return instructions."""
    url = f"{CLOUD_API_URL}/auth/github"
    webbrowser.open(url)
    return "Opening browser for GitHub authentication..."
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
        click.echo("After authorizing, copy your API key and run:", err=True)
        click.echo("  export CALLUSE_API_KEY='cu_...'", err=True)
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

- [ ] **Step 1: Write Dockerfile**

```dockerfile
# cloud/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY cloud/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY call_use/ /app/call_use/
COPY cloud/ /app/cloud/

EXPOSE 8080
CMD ["uvicorn", "cloud.app:create_cloud_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
```

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
call-use @ git+https://github.com/agent-next/call-use.git
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
| 2 | GitHub OAuth auth | Tier 1 |
| 3 | Rate limiting + phone restrictions | Tier 1 |
| 4 | Twilio Verify phone binding | Tier 2 |
| 5 | Cloud FastAPI gateway | All |
| 6 | SDK cloud auto-detection | All |
| 7 | Deployment config | Ops |

**Total: 7 tasks, ~10 commits, ~500 lines of new code**
