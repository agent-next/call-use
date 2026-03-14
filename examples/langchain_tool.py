"""Use call-use as a LangChain tool.

pip install call-use langchain-core
"""
import json
import subprocess

from langchain_core.tools import tool


@tool
def phone_call(phone: str, instructions: str, user_info: str = "{}") -> str:
    """Make a phone call via AI agent. Returns JSON with transcript and outcome.

    Args:
        phone: Target phone number in E.164 format (e.g., +18001234567)
        instructions: What to accomplish on the call
        user_info: JSON string with context (e.g., '{"name": "Alice"}')
    """
    result = subprocess.run(
        ["call-use", "dial", phone, "-i", instructions, "-u", user_info],
        capture_output=True, text=True, timeout=660,
    )
    if result.returncode == 2:
        return json.dumps({"error": f"Input error: {result.stderr.strip()}"})
    if result.returncode != 0 and not result.stdout.strip():
        return json.dumps({"error": f"Call failed (exit {result.returncode}): {result.stderr.strip()}"})
    return result.stdout


# Usage with any LangChain agent:
# agent = create_react_agent(llm, [phone_call])
# agent.invoke({"input": "Call +18001234567 and ask about store hours"})
