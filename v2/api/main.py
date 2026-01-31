from datetime import date, datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, Integer, Column, ForeignKey, Boolean, func
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine, get_db, SessionLocal, wait_for_db
from seed import seed_all
from models import TProject, TProjectTask, MTaskTemplate, MCheckItem, MTaskCheckMap, TTimerLog, TCheckResult

from routes.admin_audit import router as admin_audit_router
from core.audit_log import audit_logger, AuditLevel
from routes.master_status import router as master_status_router

app = FastAPI(title="Minecraft Create Movie System v2 API")

app.include_router(admin_audit_router)
app.include_router(master_status_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def recalc_project_progress(db: Session, project_id: int):
    tasks = db.execute(
        select(TProjectTask.status)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.is_active == True)
    ).all()

    if not tasks:
        rate = 0.0
    else:
        score = 0.0
        for (status,) in tasks:
            if status == "完了":
                score += 1.0
            elif status == "進行中":
                score += 0.5
        rate = (score / len(tasks)) * 100.0
        print(f"Project ID: {project_id}, score: {score}, total tasks: {len(tasks)}")

    project = db.execute(
        select(TProject).where(TProject.project_id == project_id)
    ).scalar_one()
    project.progress_rate = float(round(rate, 1))

    db.commit()

@app.on_event("startup")
def on_startup():
    # ① DBが起きるまで待つ
    wait_for_db()

    # ② テーブル作成
    Base.metadata.create_all(bind=engine)

    # ③ seed投入
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


# ===== タスク③に向けて最小APIも入れておく（projects一覧が出せる） =====
class ProjectCreate(BaseModel):
    theme: str
    due_date: date | None = None


class ProjectOut(BaseModel):
    project_id: int
    theme: str
    due_date: date | None
    progress_rate: float

    class Config:
        from_attributes = True

class ProjectDetailOut(BaseModel):
    project_id: int
    theme: str
    due_date: date | None
    publish_scheduled_at: date | None = None
    memo: str | None = None

    class Config:
        from_attributes = True


class ProjectTaskOut(BaseModel):
    project_task_id: int
    project_id: int
    task_template_id: int
    task_name: str
    status: str
    est_time_min: int
    actual_time_min: float
    sort_order: int
    is_active: bool

@app.get("/v2/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.execute(select(TProject).order_by(TProject.project_id.desc())).scalars().all()

    audit_logger.log(
        level=AuditLevel.INFO,
        action="プロジェクト一覧取得",
        target_type="/get /v2/projects",
        target_id=str(),
        summary="プロジェクト一覧を取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return projects


@app.post("/v2/projects", response_model=ProjectOut)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    try:
        with db.begin():
            # 1) project 作成（commitしない）
            p = TProject(theme=body.theme, due_date=body.due_date)
            db.add(p)
            db.flush()  # ← ここで p.project_id を確定させる（commitはまだ）

            # 2) task templates から project_tasks 自動生成
            templates = db.execute(
                select(MTaskTemplate)
                .where(MTaskTemplate.is_active == True)
                .order_by(MTaskTemplate.sort_order.asc())
            ).scalars().all()

            p.progress_rate = 0.0

            for t in templates:
                db.add(TProjectTask(
                    project_id=p.project_id,
                    task_template_id=t.task_template_id,
                    task_name_snapshot=t.task_name,
                    phase_id_snapshot=t.phase_id,
                    status="未着手",
                    est_time_min_snapshot=t.est_time_min,
                    actual_time_min=0.0,
                    sort_order=t.sort_order,
                    is_active=True,
                ))

        # ↑ with を抜けた時点で commit 済み

        # refresh は必要なら（返却に最新状態を入れたい場合）
        db.refresh(p)

        # 監査ログは「DB確定後」に書く（ロールバックと矛盾しない）
        audit_logger.log(
            level=AuditLevel.INFO,
            action="/post /v2/projects",
            target_type="プロジェクト作成",
            target_id=str(p.project_id) if getattr(p, "project_id", None) is not None else "",
            summary="プロジェクトを作成しました。",
            detail={"version": "なし", "change_note": "なし"},
        )

        return p

    except Exception as e:
        # db.begin が自動 rollback 済み
        audit_logger.log(
            level=AuditLevel.ERROR,
            action="/post /v2/projects",
            target_type="プロジェクト作成失敗",
            target_id=str(),
            summary="プロジェクト作成に失敗しました。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=500, detail=f"create_project failed: {str(e)}")

@app.get("/v2/projects/{project_id}", response_model=ProjectDetailOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.execute(
        select(TProject).where(TProject.project_id == project_id)
    ).scalar_one_or_none()

    if not p:
        audit_logger.log(
            level=AuditLevel.ERROR,
            action="/get /v2/projects/{project_id}",
            target_type="プロジェクト取得失敗",
            target_id=str(),
            summary="プロジェクトが見つかりませんでした。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Project not found")
    
    audit_logger.log(
        level=AuditLevel.INFO,
        action="/get /v2/projects/{project_id}",
        target_type="プロジェクト取得",
        target_id=str(),
        summary="プロジェクト" + str(project_id) + "を取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return p


@app.get("/v2/projects/{project_id}/tasks/list", response_model=list[ProjectTaskOut])
def list_project_tasks(project_id: int, db: Session = Depends(get_db)):
    # project存在チェック（親が無いのに tasks だけ返さない）
    p = db.execute(select(TProject.project_id).where(TProject.project_id == project_id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.is_active == True)
        .order_by(TProjectTask.sort_order.asc(), TProjectTask.project_task_id.asc())
    ).scalars().all()

    # APIの返却名をUI向けに整形
    result: list[ProjectTaskOut] = []
    for t in tasks:
        result.append(ProjectTaskOut(
            project_task_id=t.project_task_id,
            project_id=t.project_id,
            task_template_id=t.task_template_id,
            task_name=t.task_name_snapshot,
            status=t.status,
            est_time_min=t.est_time_min_snapshot,
            actual_time_min=t.actual_time_min,
            sort_order=t.sort_order,
            is_active=t.is_active,
        ))
    
    audit_logger.log(
        level=AuditLevel.INFO,
        action="/get /v2/projects/{project_id}/tasks/list",
        target_type="プロジェクトタスク一覧取得",
        target_id=str(),
        summary="プロジェクトタスク一覧を取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )
    return result

ALLOWED_STATUSES = ["未着手", "進行中", "完了"]

class TaskStatusPatch(BaseModel):
    status: str

@app.patch("/v2/projects/{project_id}/tasks/{project_task_id}", response_model=ProjectTaskOut)
def update_task_status(project_id: int, project_task_id: int, body: TaskStatusPatch, db: Session = Depends(get_db)):
    if body.status not in ALLOWED_STATUSES:
        audit_logger.log(
            level=AuditLevel.ERROR,
            action="/patch /v2/projects/{project_id}/tasks/{project_task_id}",
            target_type="プロジェクトタスクステータス変更失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのステータス変更に失敗しました。",
            detail={"version": "なし", "change_note": "ステータスが不正です: " + body.status},
        )
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    task = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.project_task_id == project_task_id)
        .where(TProjectTask.is_active == True)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_status = task.status

    # 遷移ルール（簡易）
    if task.status == "未着手" and body.status == "完了":
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/patch /v2/projects/{project_id}/tasks/{project_task_id}",
            target_type="プロジェクトタスクステータス変更失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのステータスを未着手から完了に変更しようとしましたが、ガードされました。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=400, detail="Cannot move 未着手 -> 完了 directly")
    if task.status == "完了" and body.status == "未着手":
        audit_logger.log(
            level=AuditLevel.WARNING,
            action="/patch /v2/projects/{project_id}/tasks/{project_task_id}",
            target_type="プロジェクトタスクステータス変更失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのステータスを完了から未着手に変更しようとしましたが、ガードされました。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=400, detail="Cannot move 完了 -> 未着手 directly")

    # ✅ 完了ガード（ここがインデント崩れやすい）
    if body.status == "完了":
        check_items = db.execute(
            select(MCheckItem.check_item_id, MCheckItem.label)
            .join(MTaskCheckMap, MTaskCheckMap.check_item_id == MCheckItem.check_item_id)
            .where(MTaskCheckMap.task_template_id == task.task_template_id)
            .where(MCheckItem.is_active == True)
        ).all()

        # チェック項目がある場合のみガードする
        if len(check_items) > 0:
            checked = db.execute(
                select(TCheckResult.check_item_id)
                .where(TCheckResult.project_task_id == task.project_task_id)
                .where(TCheckResult.is_checked == True)
            ).all()
            checked_ids = {c[0] for c in checked}

            missing = [
                {"check_item_id": cid, "label": label}
                for cid, label in check_items
                if cid not in checked_ids
            ]
            if missing:
                raise HTTPException(
                    status_code=409,
                    detail={"can_complete": False, "missing": missing}
                )

    task.status = body.status
    db.commit()
    db.refresh(task)

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/patch /v2/projects/{project_id}/tasks/{project_task_id}",
        target_type="プロジェクトタスクステータス変更",
        target_id=str(project_task_id),
        summary="プロジェクトタスクのステータスを変更しました。",
        detail={"version": "なし", "change_note": old_status + " -> " + body.status},
    )

    recalc_project_progress(db, project_id)

    return ProjectTaskOut(
        project_task_id=task.project_task_id,
        project_id=task.project_id,
        task_template_id=task.task_template_id,
        task_name=task.task_name_snapshot,
        status=task.status,
        est_time_min=task.est_time_min_snapshot,
        actual_time_min=task.actual_time_min,
        sort_order=task.sort_order,
        is_active=task.is_active,
    )

class ChecklistItemOut(BaseModel):
    check_item_id: int
    label: str
    is_checked: bool

@app.get("/v2/projects/{project_id}/tasks/{project_task_id}/checklist", response_model=list[ChecklistItemOut])
def get_task_checklist(project_id: int, project_task_id: int, db: Session = Depends(get_db)):
    task = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.project_task_id == project_task_id)
        .where(TProjectTask.is_active == True)
    ).scalar_one_or_none()
    if not task:
        audit_logger.log(
            level=AuditLevel.ERROR,
            action="/get /v2/projects/{project_id}/tasks/{project_task_id}/checklist",
            target_type="プロジェクトタスクチェックリスト取得失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのチェックリスト取得に失敗しました。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Task not found")

    # テンプレに紐づくチェック項目
    check_items = db.execute(
        select(MCheckItem)
        .join(MTaskCheckMap, MTaskCheckMap.check_item_id == MCheckItem.check_item_id)
        .where(MTaskCheckMap.task_template_id == task.task_template_id)
        .where(MCheckItem.is_active == True)
        .order_by(MCheckItem.sort_order.asc(), MCheckItem.check_item_id.asc())
    ).scalars().all()

    # 既存の結果
    results = db.execute(
        select(TCheckResult).where(TCheckResult.project_task_id == project_task_id)
    ).scalars().all()
    result_map = {r.check_item_id: r.is_checked for r in results}

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/get /v2/projects/{project_id}/tasks/{project_task_id}/checklist",
        target_type="プロジェクトタスクチェックリスト取得",
        target_id=str(project_task_id),
        summary="プロジェクトタスクのチェックリストを取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    # 結果が無いものは false で返す
    return [
        ChecklistItemOut(
            check_item_id=ci.check_item_id,
            label=ci.label,
            is_checked=bool(result_map.get(ci.check_item_id, False)),
        )
        for ci in check_items
    ]

class ChecklistUpdateItem(BaseModel):
    check_item_id: int
    is_checked: bool

@app.put("/v2/projects/{project_id}/tasks/{project_task_id}/checklist", response_model=list[ChecklistItemOut])
def update_task_checklist(project_id: int, project_task_id: int, body: list[ChecklistUpdateItem], db: Session = Depends(get_db)):
    task = db.execute(
        select(TProjectTask)
        .where(TProjectTask.project_id == project_id)
        .where(TProjectTask.project_task_id == project_task_id)
        .where(TProjectTask.is_active == True)
    ).scalar_one_or_none()
    if not task:
        audit_logger.log(
            level=AuditLevel.ERROR,
            action="/put /v2/projects/{project_id}/tasks/{project_task_id}/checklist",
            target_type="プロジェクトタスクチェックリスト更新失敗",
            target_id=str(project_task_id),
            summary="プロジェクトタスクのチェックリストが見つかりませんでした。",
            detail={"version": "なし", "change_note": "なし"},
        )
        raise HTTPException(status_code=404, detail="Task not found")

    # 更新
    for item in body:
        row = db.execute(
            select(TCheckResult)
            .where(TCheckResult.project_task_id == project_task_id)
            .where(TCheckResult.check_item_id == item.check_item_id)
        ).scalar_one_or_none()

        if row:
            row.is_checked = item.is_checked
        else:
            db.add(TCheckResult(
                project_task_id=project_task_id,
                check_item_id=item.check_item_id,
                is_checked=item.is_checked
            ))

    db.commit()

    audit_logger.log(
        level=AuditLevel.INFO,
        action="/put /v2/projects/{project_id}/tasks/{project_task_id}/checklist",
        target_type="プロジェクトタスクチェックリスト更新",
        target_id=str(project_task_id),
        summary="プロジェクトタスクのチェックリストを更新しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    # 更新後の一覧を返す
    return get_task_checklist(project_id, project_task_id, db)

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

@app.get("/v2/dashboard/workload")
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

