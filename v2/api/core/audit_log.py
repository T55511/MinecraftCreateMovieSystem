from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Dict
import traceback

class AuditLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass(frozen=True)
class AuditEvent:
    timestamp: str                 # ISO8601 UTC
    level: AuditLevel
    actor: str                     # 今は "local-user" 固定でもOK
    action: str                    # 例: CREATE_TEMPLATE_VERSION, SET_LATEST, DISABLE
    target_type: str               # 例: tpl_project_template
    target_id: Optional[str]       # uuid or status_key etc
    summary: str                   # 短文
    detail: Optional[Dict[str, Any]] = None  # 差分や入力など（個人情報は入れない）

class AuditLogger:
    """
    JSONL(1行1JSON)で監査ログを追記するロガー。
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
    ) -> None:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
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


# グローバルに使うならここで生成（DIしたいならFastAPIのDependsにしてもOK）
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "./logs/audit.log")
audit_logger = AuditLogger(AUDIT_LOG_PATH)
