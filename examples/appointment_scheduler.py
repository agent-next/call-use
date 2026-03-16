"""Example: Appointment Scheduler — calls a doctor's office to book an appointment.

Navigates IVR menus, provides patient information, and confirms appointment details.
Uses an approval flow so the user can confirm before the booking is finalized.

Usage:
    python examples/appointment_scheduler.py "+18005551234" "Schedule a checkup for next week"
"""
import asyncio
import sys
from call_use import CallAgent


PATIENT_INFO = {
    "name": "Jane Smith",
    "date_of_birth": "1985-04-12",
    "insurance": "BlueCross #BC987654321",
    "phone": "+15559876543",
    "preferred_doctor": "Dr. Patel",
}


async def main():
    if len(sys.argv) < 3:
        print("Usage: python examples/appointment_scheduler.py <phone> <task>")
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
        # Surface the proposed appointment details before committing
        print(f"\n  APPROVAL NEEDED: {details.get('details', '')}")
        print("  Review the proposed appointment above.")
        response = input("  Confirm booking? (y/n): ").strip().lower()
        return "approved" if response == "y" else "rejected"

    agent = CallAgent(
        phone=phone,
        instructions=(
            f"{task}. Navigate IVR menus by selecting the 'appointments' option. "
            "Provide patient information when prompted. If asked to confirm the "
            "appointment, request human approval before saying yes."
        ),
        user_info=PATIENT_INFO,
        on_event=on_event,
        on_approval=on_approval,
    )

    print(f"Calling {phone} to schedule appointment...")
    outcome = await agent.call()

    print("\n--- Call Complete ---")
    print(f"Duration:    {outcome.duration_seconds:.1f}s")
    print(f"Disposition: {outcome.disposition.value}")
    print(f"Transcript:  {len(outcome.transcript)} turns")


if __name__ == "__main__":
    asyncio.run(main())
