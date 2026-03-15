"""Tests for call_use.evidence.EvidencePipeline."""

import json
import os
import stat

import pytest

from call_use.evidence import EvidencePipeline
from call_use.models import (
    CallEvent,
    CallEventType,
    CallOutcome,
    CallStateEnum,
    CallTask,
    DispositionEnum,
)

pytestmark = pytest.mark.unit


def _make_task() -> CallTask:
    return CallTask(phone_number="+12125551234", instructions="test")


def _make_pipeline() -> EvidencePipeline:
    return EvidencePipeline(task=_make_task(), room_name=None)


# ---- Tests ----


@pytest.mark.asyncio
async def test_events_accumulate_in_order():
    pipe = _make_pipeline()
    await pipe.emit(CallEvent(type=CallEventType.dtmf, data={"keys": "1"}))
    await pipe.emit(CallEvent(type=CallEventType.dtmf, data={"keys": "2"}))
    await pipe.emit(CallEvent(type=CallEventType.dtmf, data={"keys": "3"}))
    assert len(pipe._events) == 3
    assert [e.data["keys"] for e in pipe._events] == ["1", "2", "3"]


@pytest.mark.asyncio
async def test_transcript_populates_both_lists():
    pipe = _make_pipeline()
    await pipe.emit_transcript("agent", "Hello")
    await pipe.emit_transcript("human", "Hi there")
    # _transcript list
    assert len(pipe._transcript) == 2
    assert pipe._transcript[0]["speaker"] == "agent"
    assert pipe._transcript[1]["text"] == "Hi there"
    # _events list
    assert len(pipe._events) == 2
    assert all(e.type == CallEventType.transcript for e in pipe._events)


@pytest.mark.asyncio
async def test_state_change_recorded():
    pipe = _make_pipeline()
    await pipe.emit_state_change(CallStateEnum.created, CallStateEnum.dialing)
    assert len(pipe._events) == 1
    ev = pipe._events[0]
    assert ev.type == CallEventType.state_change
    assert ev.data["from"] == "created"
    assert ev.data["to"] == "dialing"


@pytest.mark.asyncio
async def test_multiple_subscribers():
    pipe = _make_pipeline()
    received_a: list[CallEvent] = []
    received_b: list[CallEvent] = []

    async def sub_a(event: CallEvent):
        received_a.append(event)

    async def sub_b(event: CallEvent):
        received_b.append(event)

    pipe.subscribe(sub_a)
    pipe.subscribe(sub_b)
    await pipe.emit_dtmf("5")
    assert len(received_a) == 1
    assert len(received_b) == 1
    assert received_a[0].data["keys"] == "5"


@pytest.mark.asyncio
async def test_subscriber_exception_doesnt_break():
    pipe = _make_pipeline()
    received: list[CallEvent] = []

    async def bad_sub(event: CallEvent):
        raise RuntimeError("boom")

    async def good_sub(event: CallEvent):
        received.append(event)

    pipe.subscribe(bad_sub)
    pipe.subscribe(good_sub)
    await pipe.emit_dtmf("9")
    # good_sub still received the event despite bad_sub raising
    assert len(received) == 1
    # pipeline itself still recorded the event
    assert len(pipe._events) == 1


@pytest.mark.asyncio
async def test_finalize_returns_outcome():
    pipe = _make_pipeline()
    await pipe.emit_transcript("agent", "Hello")
    await pipe.emit_state_change(CallStateEnum.created, CallStateEnum.connected)
    outcome = pipe.finalize(DispositionEnum.completed)
    assert isinstance(outcome, CallOutcome)
    assert outcome.disposition == DispositionEnum.completed
    assert outcome.duration_seconds > 0
    assert len(outcome.transcript) == 1
    assert len(outcome.events) == 2
    assert outcome.task_id == pipe.task.task_id


@pytest.mark.asyncio
async def test_finalize_writes_json(tmp_path, monkeypatch):
    # Redirect LOGS_DIR to tmp_path so we don't pollute the real logs dir
    monkeypatch.setattr("call_use.evidence.LOGS_DIR", tmp_path)
    pipe = _make_pipeline()
    await pipe.emit_transcript("agent", "Hi")
    pipe.finalize(DispositionEnum.completed)
    log_file = tmp_path / f"{pipe.task.task_id}.json"
    assert log_file.exists()
    data = json.loads(log_file.read_text())
    assert data["task_id"] == pipe.task.task_id
    assert data["disposition"] == "completed"


@pytest.mark.asyncio
async def test_finalize_log_file_permissions(tmp_path, monkeypatch):
    """Log files containing PII must be owner-only (0600)."""
    monkeypatch.setattr("call_use.evidence.LOGS_DIR", tmp_path)
    pipe = _make_pipeline()
    await pipe.emit_transcript("agent", "Hi")
    pipe.finalize(DispositionEnum.completed)
    log_file = tmp_path / f"{pipe.task.task_id}.json"
    assert log_file.exists()
    mode = stat.S_IMODE(os.stat(log_file).st_mode)
    assert mode == 0o600, f"Expected 0600, got {oct(mode)}"
    # Directory must also be restricted to owner-only
    dir_mode = stat.S_IMODE(os.stat(tmp_path).st_mode)
    assert dir_mode == 0o700, f"Expected dir 0700, got {oct(dir_mode)}"


@pytest.mark.asyncio
async def test_finalize_twice_is_safe():
    """Calling finalize twice should not crash or duplicate."""
    pipe = _make_pipeline()
    await pipe.emit_transcript("agent", "Hello")
    outcome1 = pipe.finalize(DispositionEnum.completed)
    outcome2 = pipe.finalize(DispositionEnum.failed)
    # Both calls should succeed and share the same task_id
    assert outcome1.task_id == outcome2.task_id


@pytest.mark.asyncio
async def test_finalize_handles_log_write_failure(monkeypatch):
    """finalize handles log write failure gracefully (logs warning, still returns outcome)."""
    # Make LOGS_DIR point to an invalid path to trigger the except branch
    monkeypatch.setattr(
        "call_use.evidence.LOGS_DIR",
        type(
            "FakePath",
            (),
            {
                "mkdir": staticmethod(
                    lambda **kw: (_ for _ in ()).throw(PermissionError("no perms"))
                ),
            },
        )(),
    )
    pipe = _make_pipeline()
    await pipe.emit_transcript("agent", "Hi")
    outcome = pipe.finalize(DispositionEnum.completed)
    assert isinstance(outcome, CallOutcome)
    assert outcome.disposition == DispositionEnum.completed


@pytest.mark.asyncio
async def test_empty_pipeline_finalizes():
    pipe = _make_pipeline()
    outcome = pipe.finalize(DispositionEnum.cancelled)
    assert isinstance(outcome, CallOutcome)
    assert outcome.disposition == DispositionEnum.cancelled
    assert outcome.transcript == []
    assert outcome.events == []
    assert outcome.duration_seconds >= 0
