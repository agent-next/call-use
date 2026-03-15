"""Example: Insurance Claim — calls an insurance company to file a claim.

Navigates a complex IVR, provides policy and incident details, handles hold/transfer
to a claims specialist, and records the claim number from the call.

Usage:
    python examples/insurance_claim.py "+18005551234"
"""
import asyncio
import re
import sys
from call_use import CallAgent


CLAIM_INFO = {
    "name": "Robert Johnson",
    "policy_number": "POL-00123456",
    "date_of_birth": "1978-09-03",
    "incident_date": "2026-03-10",
    "incident_description": (
        "Minor fender bender in a parking lot. Other driver accepted fault. "
        "Damage to front bumper, estimated $1,200."
    ),
    "vehicle": "2022 Honda Accord, VIN 1HGBH41JXMN109186",
}


async def main():
    phone = sys.argv[1] if len(sys.argv) > 1 else "+18005551234"

    # Collect the claim number from the transcript as the call progresses
    claim_number: str | None = None

    def on_event(event):
        nonlocal claim_number
        if event.type.value == "transcript":
            speaker = event.data.get("speaker", "?")
            text = event.data.get("text", "")
            print(f"  [{speaker}] {text}")
            # Extract claim number mentioned by the representative
            if speaker.lower() in ("agent", "representative", "them"):
                match = re.search(r"\bCLM[-\s]?\d{6,10}\b", text, re.IGNORECASE)
                if match and claim_number is None:
                    claim_number = match.group(0).upper().replace(" ", "")
                    print(f"  ** Claim number captured: {claim_number} **")
        elif event.type.value == "state_change":
            state = event.data.get("to", "")
            print(f"  State -> {state}")
            if state == "on_hold":
                print("  (on hold — waiting for claims specialist)")

    def on_approval(details):
        print(f"\n  APPROVAL NEEDED: {details.get('details', '')}")
        response = input("  Approve? (y/n): ").strip().lower()
        return "approved" if response == "y" else "rejected"

    agent = CallAgent(
        phone=phone,
        instructions=(
            "Call the insurance company to file a new auto insurance claim. "
            "Navigate the IVR to reach the claims department. Provide the policy "
            "number, personal details, and incident information when asked. "
            "If transferred or placed on hold, wait patiently. "
            "Once the claim is filed, repeat back the claim number for confirmation."
        ),
        user_info=CLAIM_INFO,
        on_event=on_event,
        on_approval=on_approval,
    )

    print(f"Calling {phone} to file insurance claim...")
    outcome = await agent.call()

    print("\n--- Call Complete ---")
    print(f"Duration:     {outcome.duration_seconds:.1f}s")
    print(f"Disposition:  {outcome.disposition.value}")
    print(f"Claim Number: {claim_number or '(not captured — check transcript)'}")
    if outcome.summary:
        print(f"Summary:      {outcome.summary}")


if __name__ == "__main__":
    asyncio.run(main())
