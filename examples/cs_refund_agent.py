"""Example: CS Refund Agent built on call-use.

Usage:
    python examples/cs_refund_agent.py "+18001234567" "Get refund for order #12345"
"""
import asyncio
import sys
from call_use import CallAgent


async def main():
    if len(sys.argv) < 3:
        print("Usage: python examples/cs_refund_agent.py <phone> <task>")
        sys.exit(1)

    phone = sys.argv[1]
    task = sys.argv[2]

    def on_event(event):
        if event.type.value == "transcript":
            speaker = event.data.get("speaker", "?")
            text = event.data.get("text", "")
            print(f"  [{speaker}] {text}")
        elif event.type.value == "state_change":
            print(f"  State: {event.data.get('from')} -> {event.data.get('to')}")

    def on_approval(details):
        print(f"\n  APPROVAL NEEDED: {details.get('details', '')}")
        response = input("  Approve? (y/n): ").strip().lower()
        return "approved" if response == "y" else "rejected"

    agent = CallAgent(
        phone=phone,
        instructions=task,
        user_info={"name": "User"},
        on_event=on_event,
        on_approval=on_approval,
    )

    print(f"Calling {phone}...")
    outcome = await agent.call()

    print(f"\n--- Call Complete ---")
    print(f"Duration: {outcome.duration_seconds:.1f}s")
    print(f"Disposition: {outcome.disposition.value}")
    print(f"Transcript: {len(outcome.transcript)} turns")


if __name__ == "__main__":
    asyncio.run(main())
