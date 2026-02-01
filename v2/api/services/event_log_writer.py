# v2/api/services/event_log_writer.py
from __future__ import annotations

import queue
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models import TEventLog
from db import SessionLocal

_event_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=5000)
_stop_event = threading.Event()
_worker: Optional[threading.Thread] = None


def enqueue_event(event_dict: Dict[str, Any]) -> None:
    """
    DB保存は“失敗してもアプリを落とさない”のが方針。
    キューが詰まったら捨てる（一次ログ＝ファイルは残るので復元可能）。
    """
    try:
        _event_queue.put_nowait(event_dict)
    except queue.Full:
        # 捨てる（ファイルが残るので致命ではない）
        return


def _parse_ts(ts: str) -> datetime:
    # "2026-01-31T..." など ISO8601 を datetime に
    # timezone付きなら fromisoformat でOK
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _save_one(db: Session, e: Dict[str, Any]) -> None:
    stmt = insert(TEventLog).values(
        event_id=e["event_id"],
        timestamp=_parse_ts(e["timestamp"]),
        level=e["level"],
        event_type=e.get("event_type", "audit"),
        request_id=e.get("request_id"),
        actor=e.get("actor", "local-user"),
        action=e["action"],
        target_type=e["target_type"],
        target_id=e.get("target_id"),
        summary=e["summary"],
        detail=e.get("detail"),
    ).on_conflict_do_nothing(index_elements=["event_id"])
    db.execute(stmt)


def _worker_loop() -> None:
    while not _stop_event.is_set():
        try:
            e = _event_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        try:
            db = SessionLocal()
            try:
                _save_one(db, e)
                db.commit()
            finally:
                db.close()
        except Exception:
            # DB側が死んでも API を巻き込まない
            # （一次ログはファイルに残ってるので後で復元）
            pass
        finally:
            _event_queue.task_done()


def start_writer() -> None:
    global _worker
    if _worker and _worker.is_alive():
        return
    _stop_event.clear()
    _worker = threading.Thread(target=_worker_loop, name="event-log-writer", daemon=True)
    _worker.start()


def stop_writer() -> None:
    _stop_event.set()
