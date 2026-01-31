from datetime import datetime
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from db import get_db
from models import TProjectTask, TTimerLog

from core.audit_log import audit_logger, AuditLevel
from ..main import app


@app.post("/v2/projects/{project_id}/tasks/{project_task_id}/timer/start")
def start_timer(project_id: int, project_task_id: int, db: Session = Depends(get_db)):
    task = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.project_task_id == project_task_id)
        .where(TProjectTask.is_active == True)
    ).scalar_one_or_none()
    if not task:
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/post /v2/projects/{project_id}/tasks/{project_task_id}/timer/start",
            target_type="プロジェクトタスクタイマースタート失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクが見つかりません。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Task not found")

    # 既に動いているタイマーがあれば禁止
    running = db.execute(
        select(TTimerLog)
        .where(TTimerLog.project_task_id == project_task_id)
        .where(TTimerLog.end_time.is_(None))
    ).scalar_one_or_none()
    if running:
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/post /v2/projects/{project_id}/tasks/{project_task_id}/timer/start",
            target_type="プロジェクトタスクタイマースタート失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのタイマーが既に開始されています。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=409, detail="Timer already running")

    log = TTimerLog(
        project_task_id=project_task_id,
        start_time=datetime.utcnow(),
    )
    db.add(log)
    db.commit()

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/post /v2/projects/{project_id}/tasks/{project_task_id}/timer/start",
        target_type="プロジェクトタスクタイマースタート",
        target_id=str(project_task_id),
        summary="プロジェクトタスクのタイマーを開始しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return {"started": True}

@app.post("/v2/projects/{project_id}/tasks/{project_task_id}/timer/stop")
def stop_timer(project_id: int, project_task_id: int, db: Session = Depends(get_db)):
    # 親タスク存在チェック（project_idも一致させる）
    task = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.project_task_id == project_task_id)
        .where(TProjectTask.is_active == True)
    ).scalar_one_or_none()
    if not task:
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/post /v2/projects/{project_id}/tasks/{project_task_id}/timer/stop",
            target_type="プロジェクトタスクタイマーストップ失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクが見つかりません。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Task not found")

    # 実行中ログ取得
    log = db.execute(
        select(TTimerLog)
        .where(TTimerLog.project_task_id == project_task_id)
        .where(TTimerLog.end_time.is_(None))
    ).scalar_one_or_none()
    if not log:
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/post /v2/projects/{project_id}/tasks/{project_task_id}/timer/stop",
            target_type="プロジェクトタスクタイマーストップ失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのタイマーが実行中ではありません。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Running timer not found")

    end = datetime.utcnow()
    duration_min = (end - log.start_time).total_seconds() / 60.0

    log.end_time = end
    log.duration_min = float(duration_min)

    # ★ ここが重要：終了済みのみ合計（NULL混入を避ける）
    total = db.execute(
        select(func.coalesce(func.sum(TTimerLog.duration_min), 0.0))
        .where(TTimerLog.project_task_id == project_task_id)
        .where(TTimerLog.end_time.is_not(None))
        .where(TTimerLog.duration_min.is_not(None))
    ).scalar_one()

    task.actual_time_min = float(total)

    db.commit()
    db.refresh(task)

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/post /v2/projects/{project_id}/tasks/{project_task_id}/timer/stop",
        target_type="プロジェクトタスクタイマーストップ",
        target_id=str(project_task_id),
        summary="プロジェクトタスクのタイマーを停止しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return {"stopped": True, "duration_min": float(duration_min), "total_min": float(task.actual_time_min)}

@app.get("/v2/projects/{project_id}/tasks/{project_task_id}/timer/status")
def timer_status(project_id: int, project_task_id: int, db: Session = Depends(get_db)):
    # タスク存在確認
    task = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.project_task_id == project_task_id)
        .where(TProjectTask.is_active == True)
    ).scalar_one_or_none()
    if not task:
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/get /v2/projects/{project_id}/tasks/{project_task_id}/timer/status",
            target_type="プロジェクトタスクタイマーステータス取得失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクが見つかりません。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Task not found")

    running = db.execute(
        select(TTimerLog)
        .where(TTimerLog.project_task_id == project_task_id)
        .where(TTimerLog.end_time.is_(None))
        .order_by(TTimerLog.start_time.desc())
    ).scalar_one_or_none()

    if not running:
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/get /v2/projects/{project_id}/tasks/{project_task_id}/timer/status",
            target_type="プロジェクトタスクタイマーステータス取得失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのタイマーが実行中ではありません。",
            detail={"version": "なし", "change_note": "なし"},
        )
        return {"running": False}

    # 経過時間（停止してないので現在時刻で計算）
    now = datetime.utcnow()
    elapsed_min = (now - running.start_time).total_seconds() / 60.0

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/get /v2/projects/{project_id}/tasks/{project_task_id}/timer/status",
        target_type="プロジェクトタスクタイマーステータス取得成功",
        target_id=str(project_task_id),
        summary="プロジェクトタスクのタイマー状態を取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return {
        "running": True,
        "start_time": running.start_time,
        "elapsed_min": float(elapsed_min),
    }