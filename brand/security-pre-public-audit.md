# Pre-Public Audit: Sensitive Information Scan

**Repository**: call-use
**Date**: 2026-03-15
**Auditor**: Automated full-history scan
**Branches scanned**: `main`, `release/audit-v0.1.0` (identical content)
**Total commits**: ~70

## Summary

**SAFE** -- No real secrets, credentials, or sensitive personal information found in any commit across the entire git history.

Two informational findings noted below (personal email in git commits, and a public API domain reference). Neither is a blocker.

## Methodology

The following checks were performed against the **entire git history** (all branches, all commits, all diffs):

### 1. Secrets and Credentials
- **API key patterns**: Searched for `sk-`, `sk_live`, `AKIA`, `ghp_`, `glpat-` (OpenAI, Stripe, AWS, GitHub, GitLab patterns)
- **Generic secret patterns**: `api_key`, `api_secret`, `password`, `secret_key`, `private_key`, `auth_token`, `bearer`, `jwt_secret`, `session_secret`, `encryption_key`
- **Database connection strings**: `mongodb://`, `postgres://`, `mysql://`, `redis://`, `amqp://`
- **Private keys**: `BEGIN RSA`, `BEGIN DSA`, `BEGIN EC`, `BEGIN OPENSSH`, `BEGIN PGP`, `BEGIN PRIVATE`
- **Twilio Account SIDs**: `AC[a-f0-9]{32}` pattern
- **Long hex strings**: `[a-f0-9]{32,}` (potential API keys)
- **Long base64 strings**: `[A-Za-z0-9+/]{40,}={0,2}` (potential encoded secrets)

### 2. Sensitive Files
- **`.env` files**: Checked if any were ever committed (only `.env.example` exists, properly excluded by `.gitignore`)
- **`.pem`, `.key`, credentials files**: None ever committed
- **Log/database files**: None ever committed (`.log`, `.sqlite`, `.db`, `.backup`)
- **Large binary files**: Only `uv.lock` (598KB, expected lockfile)

### 3. Personal Information
- **Email addresses**: Scanned for non-standard email domains
- **Phone numbers**: Extracted and verified all phone numbers in source/doc files
- **Internal IPs**: Searched for `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x` ranges
- **Webhook URLs**: Searched for Slack, Discord webhook patterns

### 4. URLs and Endpoints
- **Internal/staging URLs**: Searched for non-public domains
- **WebSocket URLs**: Verified all `wss://` references
- **HTTP URLs**: Scanned for private API endpoints

### 5. Debug/Test Artifacts
- **Debug prints with secrets**: Checked for `print()` or `logging` calls referencing keys/secrets
- **Hardcoded test credentials**: Searched for long strings in test assertions
- **TODO/FIXME with secret references**: None found

## Findings

### Finding 1: Personal Email in Git Commits (INFORMATIONAL)

**Severity**: Informational / Personal preference
**Location**: Git commit author metadata (all commits on `main` branch except the initial squash-merge)

The email `robert.alexander37899@gmail.com` appears as the commit author email on ~68 of ~70 commits. The remaining commits use the GitHub noreply address `7380929+robotlearning123@users.noreply.github.com`.

**Assessment**: This is standard for open-source projects. The email is visible in `git log` but is the author's personal choice. If you prefer to hide it, you would need to use `git filter-branch` or `git filter-repo` to rewrite history before going public. This is a personal privacy decision, not a security issue.

**Recommendation**: If you want to anonymize, rewrite all commit author emails to the GitHub noreply address before making public. Otherwise, this is fine as-is for an open-source project.

### Finding 2: Public API Domain Reference (INFORMATIONAL)

**Severity**: Informational
**Location**: Planning documents (`docs/plans/`, `docs/superpowers/`)

The domain `api.calluse.dev` appears as a default cloud API URL:
```
CLOUD_API_URL = os.environ.get("CALLUSE_API_URL", "https://api.calluse.dev")
```

And `calluse.dev` is mentioned as an optional landing page domain.

**Assessment**: These are in planning/design documents, not in production code. The URL is a public-facing product domain, not an internal staging URL. No security concern.

### Verified Safe Items

| Category | Result |
|----------|--------|
| **OpenAI API keys** | Only placeholders: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`, `sk-...`, `sk-test`, `sk-your-openai-key` |
| **LiveKit credentials** | Only placeholders: `your-api-key`, `your-api-secret`, `key`, `secret`, `wss://test`, `APIxxxxxxxx` |
| **Deepgram API keys** | Only placeholders: `your-deepgram-key`, `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| **SIP Trunk IDs** | Only placeholders: `your-sip-trunk-id`, `trunk`, `ST_xxxxxxxxxxxxxxxxxxxxxxxx` |
| **AWS/GCP/Azure credentials** | None found |
| **Stripe/GitHub/GitLab tokens** | None found |
| **Private keys (PEM/SSH)** | None found |
| **Database connection strings** | None found |
| **Webhook URLs** | None found |
| **Internal IP addresses** | None found |
| **Phone numbers** | All synthetic test data: 555 exchange, 800/900 toll-free/premium, used appropriately in validation tests |
| **.env files committed** | Never (only `.env.example` with placeholder values) |
| **Docker/K8s secrets** | None found |
| **JWT/session secrets** | None found |
| **Log files** | Never committed; excluded by `.gitignore` |
| **Debug prints with secrets** | One `print(f"Takeover active. LiveKit token: {token[:20]}...")` -- properly truncated, and only prints first 20 chars in a runtime debug message |
| **Test fixtures** | All use synthetic values (`"key"`, `"secret"`, `"trunk"`, `"wss://test"`, `"sk-test"`) |
| **`.gitignore` coverage** | Properly excludes `.env`, `recordings/`, `logs/`, `*.wav`, `*.mp3`, `.venv/`, IDE files |

## Recommendation

**SAFE TO MAKE PUBLIC.**

No secrets, real credentials, or sensitive data were found in any commit across the entire git history.

The only decision point is whether you want to rewrite git history to replace the personal email address (`robert.alexander37899@gmail.com`) with the GitHub noreply address. This is a personal privacy preference, not a security requirement.

### Optional Pre-Public Cleanup

If you want to sanitize the email:
```bash
git filter-repo --mailmap <(echo "robolearning123 <7380929+robotlearning123@users.noreply.github.com> robolearning123 <robert.alexander37899@gmail.com>")
```

This would rewrite all commits to use the noreply address. Note: this changes commit hashes and requires a force push.
