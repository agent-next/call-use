"""Example: Webhook Integration — FastAPI app that creates calls and streams results.

Exposes two endpoints:
  POST /calls          — start a call, returns call_id
  GET  /calls/{id}     — poll for status / result
  WS   /calls/{id}/ws  — stream live events over WebSocket

Demonstrates a real-world server-side integration pattern.

pip install call-use fastapi uvicorn websockets
Run: uvicorn examples.webhook_integration:app --reload
"""
import asyncio
import uuid
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from call_use import CallAgent

app = FastAPI(title="call-use webhook demo")

# In-memory store: call_id -> {status, outcome, events}
_calls: dict[str, dict[str, Any]] = {}
# WebSocket subscribers: call_id -> list of queues
_subscribers: dict[str, list[asyncio.Queue]] = {}


class CallRequest(BaseModel):
    phone: str
    instructions: str
    user_info: dict[str, str] = {}


async def _run_call(call_id: str, req: CallRequest):
    """Background task: runs the agent and updates the store."""
    _calls[call_id]["status"] = "in_progress"

    def on_event(event):
        ev = {"type": event.type.value, "data": event.data}
        _calls[call_id]["events"].append(ev)
        # Fan-out to all WebSocket subscribers
        for q in _subscribers.get(call_id, []):
            q.put_nowait(ev)

    agent = CallAgent(
        phone=req.phone,
        instructions=req.instructions,
        user_info=req.user_info,
        on_event=on_event,
        approval_required=False,
    )

    try:
        outcome = await agent.call()
        _calls[call_id]["status"] = "completed"
        _calls[call_id]["outcome"] = {
            "disposition": outcome.disposition.value,
            "duration_seconds": outcome.duration_seconds,
            "transcript": outcome.transcript,
        }
    except Exception as exc:
        _calls[call_id]["status"] = "error"
        _calls[call_id]["error"] = str(exc)
    finally:
        # Signal EOF to all subscribers
        for q in _subscribers.get(call_id, []):
            q.put_nowait(None)


@app.post("/calls", status_code=202)
async def create_call(req: CallRequest):
    """Start a new call. Returns immediately with a call_id."""
    call_id = str(uuid.uuid4())
    _calls[call_id] = {"status": "pending", "events": [], "outcome": None}
    asyncio.create_task(_run_call(call_id, req))
    return JSONResponse({"call_id": call_id, "status": "pending"})


@app.get("/calls/{call_id}")
async def get_call(call_id: str):
    """Poll for call status and result."""
    record = _calls.get(call_id)
    if not record:
        raise HTTPException(status_code=404, detail="call not found")
    return record


@app.websocket("/calls/{call_id}/ws")
async def call_events_ws(websocket: WebSocket, call_id: str):
    """Stream live events for a call over WebSocket."""
    if call_id not in _calls:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(call_id, []).append(queue)

    # Replay any events that already happened
    for ev in _calls[call_id]["events"]:
        await websocket.send_json(ev)

    try:
        while True:
            ev = await queue.get()
            if ev is None:  # call finished
                break
            await websocket.send_json(ev)
    except WebSocketDisconnect:
        pass
    finally:
        _subscribers[call_id].remove(queue)
        await websocket.close()
