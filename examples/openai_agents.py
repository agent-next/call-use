"""Use call-use as an OpenAI Agents SDK tool.

pip install call-use openai-agents
"""

import json
import subprocess

from agents import Agent, function_tool


@function_tool
def phone_call(phone: str, instructions: str, user_info: str = "{}") -> str:
    """Make a phone call via AI agent. Returns JSON with transcript and outcome.

    Args:
        phone: Target phone number in E.164 format (e.g., +18001234567)
        instructions: What to accomplish on the call
        user_info: JSON string with context (e.g., '{"name": "Alice"}')
    """
    try:
        result = subprocess.run(
            ["call-use", "dial", phone, "-i", instructions, "-u", user_info],
            capture_output=True,
            text=True,
            timeout=660,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Call timed out after 660 seconds"})
    if result.returncode == 2:
        return json.dumps({"error": f"Input error: {result.stderr.strip()}"})
    if result.returncode != 0 and not result.stdout.strip():
        return json.dumps(
            {"error": f"Call failed (exit {result.returncode}): {result.stderr.strip()}"}
        )
    return result.stdout


agent = Agent(
    name="Phone Agent",
    instructions="You help users by making phone calls on their behalf.",
    tools=[phone_call],
)

# Usage:
# Runner.run_sync(agent, "Call Comcast at +18001234567 and cancel my subscription")
