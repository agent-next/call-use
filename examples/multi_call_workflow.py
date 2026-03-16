"""Example: Multi-Call Workflow — orchestrates sequential calls based on results.

Call 1: Check account status with the bank (balance inquiry).
Call 2: If the balance is below a threshold, call the credit card company
        to request a credit limit increase.

Demonstrates how to chain CallAgent calls and pass data between them.

Usage:
    python examples/multi_call_workflow.py
"""
import asyncio
import re
from call_use import CallAgent


# Fake phone numbers for illustration
BANK_PHONE = "+18005551001"
CREDIT_CARD_PHONE = "+18005551002"

USER_INFO = {
    "name": "David Lee",
    "account_last_four": "4821",
    "date_of_birth": "1990-07-22",
    "ssn_last_four": "6789",
}

LOW_BALANCE_THRESHOLD = 500.0  # dollars


def make_transcript_printer(label: str):
    def on_event(event):
        if event.type.value == "transcript":
            speaker = event.data.get("speaker", "?")
            text = event.data.get("text", "")
            print(f"  [{label}] [{speaker}] {text}")
        elif event.type.value == "state_change":
            print(f"  [{label}] State -> {event.data.get('to')}")
    return on_event


def extract_balance(transcript: list) -> float | None:
    """Parse the balance from transcript turns."""
    for turn in transcript:
        text = turn.get("text", "")
        # Match patterns like "$1,234.56" or "1234 dollars"
        match = re.search(r"\$?([\d,]+(?:\.\d{2})?)\s*(?:dollars?)?", text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


async def call_1_check_balance() -> float | None:
    """Call 1: Check checking account balance."""
    print(f"\n=== Call 1: Balance Check ({BANK_PHONE}) ===")

    agent = CallAgent(
        phone=BANK_PHONE,
        instructions=(
            "Call the bank's automated line and check the current balance "
            "on the checking account ending in 4821. Navigate the IVR to "
            "'account balance', listen carefully, and repeat the balance aloud."
        ),
        user_info=USER_INFO,
        on_event=make_transcript_printer("Bank"),
    )

    outcome = await agent.call()
    print(f"  Disposition: {outcome.disposition.value}")

    balance = extract_balance(outcome.transcript)
    if balance is not None:
        print(f"  Detected balance: ${balance:,.2f}")
    else:
        print("  Could not parse balance from transcript.")
    return balance


async def call_2_request_credit_increase(current_balance: float):
    """Call 2: Request a credit limit increase because balance is low."""
    print(f"\n=== Call 2: Credit Limit Increase ({CREDIT_CARD_PHONE}) ===")
    print(f"  Reason: balance ${current_balance:,.2f} is below ${LOW_BALANCE_THRESHOLD:,.2f}")

    def on_approval(details):
        print(f"\n  APPROVAL: {details.get('details', '')}")
        response = input("  Approve? (y/n): ").strip().lower()
        return "approved" if response == "y" else "rejected"

    agent = CallAgent(
        phone=CREDIT_CARD_PHONE,
        instructions=(
            "Call the credit card company to request a credit limit increase. "
            "Explain that I would like a higher limit for upcoming expenses. "
            "If asked to confirm or accept new terms, request human approval first."
        ),
        user_info={**USER_INFO, "reason": "upcoming travel expenses"},
        on_event=make_transcript_printer("CreditCard"),
        on_approval=on_approval,
    )

    outcome = await agent.call()
    print(f"  Disposition: {outcome.disposition.value}")
    print(f"  Transcript: {len(outcome.transcript)} turns")


async def main():
    # --- Call 1 ---
    balance = await call_1_check_balance()

    # --- Decision gate ---
    if balance is None:
        print("\nCould not determine balance — skipping follow-up call.")
        return

    if balance >= LOW_BALANCE_THRESHOLD:
        print(f"\nBalance ${balance:,.2f} is healthy. No follow-up needed.")
        return

    # --- Call 2 (conditional) ---
    await call_2_request_credit_increase(balance)

    print("\n=== Workflow Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
