"""Example: Subscription Cancellation — calls to cancel a gym or ISP subscription.

Handles retention offers (discounts, pauses, free months) via approval flow so the
user decides whether to accept or reject them. Persists through transfers.

Usage:
    python examples/subscription_cancellation.py "+18005551234" "gym"
"""
import asyncio
import sys
from call_use import CallAgent


ACCOUNT_INFO = {
    "name": "Maria Garcia",
    "account_number": "GYM-7734821",
    "email": "maria.garcia@example.com",
    "reason_for_cancellation": "Relocating to a city without a nearby branch",
}


def build_instructions(service_type: str) -> str:
    return (
        f"Call to cancel my {service_type} subscription. "
        "When asked for a reason, say I am relocating. "
        "If the representative offers a discount, free months, or a pause — "
        "do NOT accept immediately; request human approval first. "
        "If transferred to a retention specialist, remain firm and polite. "
        "Confirm the cancellation effective date and any final charges before hanging up."
    )


async def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/subscription_cancellation.py <phone> [service_type]")
        sys.exit(1)

    phone = sys.argv[1]
    service_type = sys.argv[2] if len(sys.argv) > 2 else "subscription"

    retention_offers: list[str] = []

    def on_event(event):
        if event.type.value == "transcript":
            speaker = event.data.get("speaker", "?")
            text = event.data.get("text", "")
            print(f"  [{speaker}] {text}")
        elif event.type.value == "state_change":
            state = event.data.get("to", "")
            print(f"  State -> {state}")
            if state == "transferred":
                print("  (transferred — likely to retention department)")

    def on_approval(details):
        detail_text = details.get("details", "")
        print(f"\n  RETENTION OFFER: {detail_text}")
        retention_offers.append(detail_text)
        print("  Options: (y) accept offer  (n) decline and proceed with cancellation")
        response = input("  Accept offer? (y/n): ").strip().lower()
        return "approved" if response == "y" else "rejected"

    agent = CallAgent(
        phone=phone,
        instructions=build_instructions(service_type),
        user_info=ACCOUNT_INFO,
        on_event=on_event,
        on_approval=on_approval,
    )

    print(f"Calling {phone} to cancel {service_type} subscription...")
    outcome = await agent.call()

    print("\n--- Call Complete ---")
    print(f"Duration:        {outcome.duration_seconds:.1f}s")
    print(f"Disposition:     {outcome.disposition.value}")
    print(f"Offers received: {len(retention_offers)}")
    for i, offer in enumerate(retention_offers, 1):
        print(f"  Offer {i}: {offer}")
    print(f"Transcript:      {len(outcome.transcript)} turns")


if __name__ == "__main__":
    asyncio.run(main())
