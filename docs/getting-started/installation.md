# Installation

## Install from PyPI

```bash
pip install call-use
```

This installs the `call-use` package along with all required dependencies:

- LiveKit Agents SDK (v1.4+)
- LiveKit plugins for OpenAI, Deepgram, noise cancellation, and Silero VAD
- FastAPI + Uvicorn (for the REST API)
- Click (for the CLI)
- MCP server framework
- Pydantic v2

## System requirements

| Requirement | Version |
|------------|---------|
| Python | 3.11+ |
| OS | macOS, Linux, Windows (WSL recommended) |
| Network | Outbound HTTPS + WSS access |

## Verify installation

After installing, verify the CLI is available:

```bash
call-use --version
```

You should see the installed version number (e.g., `call-use, version 0.1.0`).

## Install for development

If you want to contribute or run from source:

```bash
git clone https://github.com/agent-next/call-use.git
cd call-use
pip install -e ".[dev]"
```

The `dev` extras include pytest, pytest-asyncio, pytest-cov, httpx, and mypy.

Run the test suite to verify everything works:

```bash
make test
```

## Entry points

The package installs three CLI commands:

| Command | Purpose |
|---------|---------|
| `call-use` | CLI for making calls (`call-use dial ...`) |
| `call-use-worker` | LiveKit agent worker process |
| `call-use-mcp` | MCP server for AI agent integration |

## Next steps

[:octicons-arrow-right-24: Configure your environment](configuration.md)
