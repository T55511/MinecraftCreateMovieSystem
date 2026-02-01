from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from services.event_log_writer import enqueue_event


class AuditLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class EventType(str, Enum):
    AUDIT = "audit"
    ERROR = "error"
    VALIDATION = "validation"
    SYSTEM = "system"


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str  # ISO8601 UTC
    level: AuditLevel
    event_type: EventType  # audit / error / validation / system
    request_id: Optional[str]  # 同一リクエストを紐付ける
    actor: str  # 今は "local-user" 固定でもOK
    action: str  # 例: POST /v2/projects
    target_type: str  # 例: project, task, template, unhandled_exception
    target_id: Optional[str]  # uuid or status_key etc
    summary: str  # 短文
    detail: Optional[Dict[str, Any]] = None  # 差分や入力など（個人情報は入れない）


class AuditLogger:
    """
    JSONL(1行1JSON)でログを追記するロガー。
    - 低コスト
    - grepしやすい
    - UIでのフィルタもしやすい
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def log(
        self,
        level: AuditLevel,
        action: str,
        target_type: str,
        target_id: Optional[str],
        summary: str,
        actor: str = "local-user",
        detail: Optional[Dict[str, Any]] = None,
        event_type: EventType = EventType.AUDIT,  # ← 追加（既存呼び出しは影響なし）
        request_id: Optional[str] = None,  # ← 追加（既存呼び出しは影響なし）
    ) -> None:
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            event_type=event_type,
            request_id=request_id,
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            summary=summary,
            detail=detail,
        )
        line = json.dumps(asdict(event), ensure_ascii=False, separators=(",", ":"))

        # 追記は排他して安全に
        with self._lock:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        # log() の末尾に追加
        data = asdict(event)

        # ファイル追記（既存のまま） ← ここが一次ログ
        with self._lock:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        # DB追随（失敗してもOK）
        enqueue_event(data)


AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "./logs/audit.log")
audit_logger = AuditLogger(AUDIT_LOG_PATH)
