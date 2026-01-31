from datetime import datetime, timedelta
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from db import get_db
from models import TProjectTask, TTimerLog

from core.audit_log import audit_logger, AuditLevel

router = APIRouter()


@router.get("/v2/dashboard/workload")
def dashboard_workload(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    start = now - timedelta(days=7)

    # 直近7日で終了したログを対象
    actual = db.execute(
        select(func.coalesce(func.sum(TTimerLog.duration_min), 0.0))
        .where(TTimerLog.end_time.is_not(None))
        .where(TTimerLog.end_time >= start)
        .where(TTimerLog.duration_min.is_not(None))
    ).scalar_one()

    # 直近7日で作業したプロジェクト（timerlog経由で project_id を引く）
    project_ids = db.execute(
        select(func.distinct(TProjectTask.project_id))
        .join(TTimerLog, TTimerLog.project_task_id == TProjectTask.project_task_id)
        .where(TTimerLog.end_time.is_not(None))
        .where(TTimerLog.end_time >= start)
    ).scalars().all()

    if project_ids:
        estimated = db.execute(
            select(func.coalesce(func.sum(TProjectTask.est_time_min_snapshot), 0))
            .where(TProjectTask.project_id.in_(project_ids))
            .where(TProjectTask.is_active == True)
        ).scalar_one()
    else:
        estimated = 0

    estimated = float(estimated)
    actual = float(actual)

    load_percent = 0.0
    if estimated > 0:
        load_percent = float(round((actual / estimated) * 100.0, 1))

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/get /v2/dashboard/workload",
        target_type="ダッシュボードワークロード取得成功",
        target_id=str(),
        summary="ダッシュボードワークロードを取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return {
        "from": start.isoformat(),
        "to": now.isoformat(),
        "actual_minutes_7d": round(actual, 1),
        "estimated_minutes_7d": round(estimated, 1),
        "load_percent": load_percent,
    }