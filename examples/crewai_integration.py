"""Example: CrewAI Integration — use call-use as a tool inside a CrewAI crew.

Defines a PhoneCallTool and wires it into a two-agent crew:
  - Researcher: gathers context before calling
  - PhoneAgent: makes the actual call and reports results

pip install call-use crewai
"""

import json
import subprocess
from typing import Type

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------


class PhoneCallInput(BaseModel):
    phone: str = Field(description="Target phone number in E.164 format, e.g. +18005551234")
    instructions: str = Field(description="What to accomplish on the call")
    user_info: str = Field(default="{}", description="JSON string with caller context")


class PhoneCallTool(BaseTool):
    name: str = "phone_call"
    description: str = (
        "Make an outbound phone call via an AI voice agent. "
        "Use this to interact with IVR systems, customer service lines, "
        "or any phone-based service. Returns a JSON summary of the call."
    )
    args_schema: Type[BaseModel] = PhoneCallInput

    def _run(self, phone: str, instructions: str, user_info: str = "{}") -> str:
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


# ---------------------------------------------------------------------------
# Crew definition
# ---------------------------------------------------------------------------

phone_tool = PhoneCallTool()

researcher = Agent(
    role="Research Analyst",
    goal="Gather all context needed before making a phone call.",
    backstory="You prepare call briefs so the phone agent has everything it needs.",
    verbose=True,
)

caller = Agent(
    role="Phone Agent",
    goal="Make phone calls on behalf of the user and report outcomes.",
    backstory="You are expert at navigating IVR menus and speaking with representatives.",
    tools=[phone_tool],
    verbose=True,
)

# ---------------------------------------------------------------------------
# Example crew (uncomment to run)
# ---------------------------------------------------------------------------

# task_research = Task(
#     description="Summarize what information is needed to cancel a gym membership.",
#     expected_output="A bullet list of required info (account number, reason, etc.).",
#     agent=researcher,
# )
#
# task_call = Task(
#     description=(
#         "Call Planet Fitness at +18005551234 and cancel the membership for "
#         "account GYM-7734821 under the name Maria Garcia."
#     ),
#     expected_output="Call outcome: disposition, claim/confirmation number, summary.",
#     agent=caller,
# )
#
# crew = Crew(agents=[researcher, caller], tasks=[task_research, task_call], verbose=True)
# result = crew.kickoff()
# print(result)
