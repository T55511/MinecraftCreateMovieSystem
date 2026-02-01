from core.audit_log import AuditLevel, audit_logger
from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from models import MTaskTemplate, TProject, TProjectTask
from schemas.project import ProjectCreate, ProjectDetailOut, ProjectOut
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/v2/projects", response_model=list[ProjectOut])
# trunk-ignore(ruff/B008)
def list_projects(db: Session = Depends(get_db)):
    projects = (
        db.execute(select(TProject).order_by(TProject.project_id.desc()))
        .scalars()
        .all()
    )

    audit_logger.log(
        level=AuditLevel.INFO,
        action="プロジェクト一覧取得",
        target_type="/get /v2/projects",
        target_id=str(),
        summary="プロジェクト一覧を取得しました。",
        detail={"version": "なし", "change_note": "なし"},
    )

    return projects


@router.post("/v2/projects", response_model=ProjectOut)
# trunk-ignore(ruff/B008)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    try:
        with db.begin():
            # 1) project 作成（commitしない）
            p = TProject(theme=body.theme, due_date=body.due_date)
            db.add(p)
            db.flush()  # ← ここで p.project_id を確定させる（commitはまだ）

            # 2) task templates から project_tasks 自動生成
            templates = (
                db.execute(
                    select(MTaskTemplate)
                    .where(MTaskTemplate.is_active.is_(True))
                    .order_by(MTaskTemplate.sort_order.asc())
                )
                .scalars()
                .all()
            )

            p.progress_rate = 0.0

            for t in templates:
                db.add(
                    TProjectTask(
                        project_id=p.project_id,
                        task_template_id=t.task_template_id,
                        task_name_snapshot=t.task_name,
                        phase_id_snapshot=t.phase_id,
                        status="未着手",
                        est_time_min_snapshot=t.est_time_min,
                        actual_time_min=0.0,
                        sort_order=t.sort_order,
                        is_active=True,
                    )
                )

        # ↑ with を抜けた時点で commit 済み

        # refresh は必要なら（返却に最新状態を入れたい場合）
        db.refresh(p)

        # 監査ログは「DB確定後」に書く（ロールバックと矛盾しない）
        audit_logger.log(
            level=AuditLevel.INFO,
            action="/post /v2/projects",
            target_type="プロジェクト作成",
            target_id=(
                str(p.project_id) if getattr(p, "project_id", None) is not None else ""
            ),
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
        # trunk-ignore(ruff/B904)
        raise HTTPException(status_code=500, detail=f"create_project failed: {str(e)}")


@router.get("/v2/projects/{project_id}", response_model=ProjectDetailOut)
# trunk-ignore(ruff/B008)
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
