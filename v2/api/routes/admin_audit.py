from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Query, HTTPException

from core.audit_log import AUDIT_LOG_PATH, AuditLevel

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit"])

def _parse_dt(s: str) -> datetime:
    # ISO8601想定（例: 2026-01-24T12:34:56+00:00）
    return datetime.fromisoformat(s)

@router.get("")
def list_audit_logs(
    # trunk-ignore(ruff/B008)
    level: Optional[AuditLevel] = Query(default=None),
    q: Optional[str] = Query(default=None, description="部分一致検索（summary/actor/action/target等）"),
    time_from: Optional[str] = Query(default=None, description="ISO8601"),
    time_to: Optional[str] = Query(default=None, description="ISO8601"),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """
    単純実装：ファイルを末尾から読みたいが、まずは全読み→フィルタでOK（重くなったら改修）
    仕様：
    - limit/offsetでページング
    - 条件フィルタ：level, q, time_from/to
    """
    try:
        tf = _parse_dt(time_from) if time_from else None
        tt = _parse_dt(time_to) if time_to else None
    except ValueError:
        # trunk-ignore(ruff/B904)
        raise HTTPException(status_code=400, detail="time_from/time_to must be ISO8601")

    rows: List[Dict[str, Any]] = []
    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    # 壊れた行はスキップ（監査ログは落とさない）
                    continue

                if level and evt.get("level") != level.value:
                    continue

                if tf or tt:
                    ts = evt.get("timestamp")
                    if not ts:
                        continue
                    try:
                        dt = _parse_dt(ts)
                    except ValueError:
                        continue
                    if tf and dt < tf:
                        continue
                    if tt and dt > tt:
                        continue

                if q:
                    hay = " ".join(
                        str(evt.get(k, "")) for k in
                        ["summary", "actor", "action", "target_type", "target_id"]
                    )
                    if q not in hay:
                        continue

                rows.append(evt)

    except FileNotFoundError:
        return {"total": 0, "items": []}

    total = len(rows)
    # 新しい順に見たいなら逆順
    rows.reverse()
    items = rows[offset: offset + limit]
    return {"total": total, "items": items}
