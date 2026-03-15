# API Reference

Auto-generated reference documentation for the call-use Python API.

## CallAgent

The main SDK entry point for making outbound calls.

::: call_use.sdk.CallAgent
    options:
      show_source: true
      members:
        - __init__
        - call
        - takeover
        - resume
        - cancel

## create_app

Factory function for the FastAPI REST API application.

::: call_use.server.create_app
    options:
      show_source: true

## Request/Response models (REST API)

### CreateCallRequest

::: call_use.server.CreateCallRequest
    options:
      show_source: false

### CreateCallResponse

::: call_use.server.CreateCallResponse
    options:
      show_source: false

### CallStatusResponse

::: call_use.server.CallStatusResponse
    options:
      show_source: false

## MCP Server

The MCP server module exposes phone calling as tools for AI agents.

### dial

::: call_use.mcp_server.dial
    options:
      show_source: true

### status

::: call_use.mcp_server.status
    options:
      show_source: true

### cancel

::: call_use.mcp_server.cancel
    options:
      show_source: true

### result

::: call_use.mcp_server.result
    options:
      show_source: true

## Evidence Pipeline

::: call_use.evidence.EvidencePipeline
    options:
      show_source: true
      members:
        - __init__
        - subscribe
        - emit
        - emit_state_change
        - emit_transcript
        - emit_dtmf
        - emit_approval_request
        - emit_approval_response
        - emit_takeover
        - emit_resume
        - emit_error
        - finalize

## Phone Validation

::: call_use.phone.validate_phone_number
    options:
      show_source: true

::: call_use.phone.validate_caller_id
    options:
      show_source: true

## Rate Limiter

::: call_use.rate_limit.RateLimiter
    options:
      show_source: true
