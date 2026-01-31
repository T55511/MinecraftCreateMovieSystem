from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from db import get_db
from models import TProject, TProjectTask, MCheckItem, MTaskCheckMap, TCheckResult

from core.audit_log import audit_logger, AuditLevel
from ..main import ChecklistItemOut, ChecklistUpdateItem, ProjectTaskOut, TaskStatusPatch, app, recalc_project_progress

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