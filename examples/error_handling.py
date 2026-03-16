"""Error handling patterns for call-use."""

import asyncio

from call_use import CallAgent, CallError


async def main():
    try:
        agent = CallAgent(
            phone="+1234567890",
            instructions="Say hello",
            approval_required=False,
        )
        outcome = await agent.call()

        if outcome.disposition.value == "failed":
            print(f"Call failed. Duration: {outcome.duration_seconds}s")
            print(f"Transcript: {outcome.transcript}")
        else:
            print(f"Call completed: {outcome.disposition.value}")

    except CallError as e:
        print(f"Call error [{e.code}]: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
