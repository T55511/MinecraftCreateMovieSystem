# v2/api/routes/master_status.py

import re
from typing import List, Optional

from core.audit_log import AuditLevel, audit_logger  # 監査ログ（既に入れてる前提）
from db import get_db  # 既存のget_dbに合わせる（なければあなたの依存に差し替え）
from fastapi import APIRouter, Depends, HTTPException, Query  # type: ignore
from schemas.status import (
    MstStatusDefinition,
    MstStatusDefinitionCreate,
    MstStatusDefinitionOut,
    MstStatusDefinitionUpdate,
    MstStatusUI,
    MstStatusUIItemIn,
    MstStatusUIItemOut,
)
from sqlalchemy.orm import Session  # type: ignore

router = APIRouter(prefix="/v2/masters/status", tags=["masters-status"])

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_color(color_hex: Optional[str]) -> None:
    if color_hex is None or color_hex == "":
        return
    if not HEX_RE.match(color_hex):
        raise HTTPException(status_code=400, detail="color_hex must be like #RRGGBB")


def _allowed_scopes_for_ui(scope: str) -> List[str]:
    # UI scope=PROJECT のとき、PROJECT + COMMON を選べる運用にする
    if scope == "PROJECT":
        return ["PROJECT", "COMMON"]
    if scope == "SUBTASK":
        return ["SUBTASK", "COMMON"]
    if scope == "COMMON":
        return ["COMMON"]
    raise HTTPException(status_code=400, detail="Invalid scope")


# ---------- Endpoints: MstStatusDefinition ----------
@router.get("/definitions", response_model=List[MstStatusDefinitionOut])
def list_definitions(
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
    scope: Optional[str] = Query(default=None, pattern=r"^(PROJECT|SUBTASK|COMMON)$"),
    active_only: bool = True,
):
    q = db.query(MstStatusDefinition)
    if scope:
        q = q.filter(MstStatusDefinition.scope == scope)
    if active_only:
        q = q.filter(MstStatusDefinition.is_active.is_(True))
    return q.order_by(
        MstStatusDefinition.scope.asc(), MstStatusDefinition.status_key.asc()
    ).all()


@router.post("/definitions", response_model=MstStatusDefinitionOut)
def create_definition(
    # trunk-ignore(ruff/B008)
    payload: MstStatusDefinitionCreate, db: Session = Depends(get_db)
):
    _validate_color(payload.color_hex)

    exists = (
        db.query(MstStatusDefinition)
        .filter(MstStatusDefinition.status_key == payload.status_key)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="status_key already exists")

    row = MstStatusDefinition(
        status_key=payload.status_key,
        display_name=payload.display_name,
        scope=payload.scope,
        is_done=payload.is_done,
        color_hex=payload.color_hex,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_logger.log(
        level=AuditLevel.INFO,
        action="CREATE_STATUS_DEFINITION",
        target_type="mst_status_definition",
        target_id=row.status_key,
        summary="Created status definition",
        detail={
            "scope": row.scope,
            "display_name": row.display_name,
            "color_hex": row.color_hex,
            "is_done": row.is_done,
        },
    )
    return row


@router.patch("/definitions/{status_key}", response_model=MstStatusDefinitionOut)
def update_definition(
    # trunk-ignore(ruff/B008)
    status_key: str, payload: MstStatusDefinitionUpdate, db: Session = Depends(get_db)
):
    _validate_color(payload.color_hex)

    row = (
        db.query(MstStatusDefinition)
        .filter(MstStatusDefinition.status_key == status_key)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="not found")

    # status_key は変更不可（仕様）
    if payload.display_name is not None:
        row.display_name = payload.display_name
    if payload.scope is not None:
        row.scope = payload.scope
    if payload.is_done is not None:
        row.is_done = payload.is_done
    if payload.color_hex is not None:
        row.color_hex = payload.color_hex
    if payload.is_active is not None:
        row.is_active = payload.is_active

    db.commit()
    db.refresh(row)

    audit_logger.log(
        level=AuditLevel.INFO,
        action="UPDATE_STATUS_DEFINITION",
        target_type="mst_status_definition",
        target_id=row.status_key,
        summary="Updated status definition",
        detail={
            "scope": row.scope,
            "display_name": row.display_name,
            "color_hex": row.color_hex,
            "is_done": row.is_done,
            "is_active": row.is_active,
        },
    )
    return row


# ---------- Endpoints: MstStatusUI ----------
@router.get("/ui", response_model=List[MstStatusUIItemOut])
def list_status_ui(
    scope: str = Query(..., pattern=r"^(PROJECT|SUBTASK|COMMON)$"),
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MstStatusUI)
        .filter(MstStatusUI.scope == scope)
        .order_by(MstStatusUI.display_order.asc(), MstStatusUI.status_key.asc())
        .all()
    )
    return rows


@router.put("/ui", response_model=List[MstStatusUIItemOut])
def upsert_status_ui(
    scope: str = Query(..., pattern=r"^(PROJECT|SUBTASK|COMMON)$"),
    # trunk-ignore(ruff/B006)
    items: List[MstStatusUIItemIn] = [],
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
):
    if not items:
        raise HTTPException(status_code=400, detail="items is required")

    # 重複チェック
    keys = [x.status_key for x in items]
    if len(set(keys)) != len(keys):
        raise HTTPException(status_code=400, detail="duplicate status_key in items")

    # 存在＆scope許容チェック
    allowed_scopes = _allowed_scopes_for_ui(scope)
    defs = (
        db.query(MstStatusDefinition)
        .filter(MstStatusDefinition.status_key.in_(keys))
        .all()
    )
    if len(defs) != len(keys):
        found = {d.status_key for d in defs}
        missing = [k for k in keys if k not in found]
        raise HTTPException(status_code=400, detail={"missing_status_keys": missing})

    for d in defs:
        if d.scope not in allowed_scopes:
            raise HTTPException(
                status_code=400,
                detail=f"status_key '{d.status_key}' scope '{d.scope}' is not allowed for UI scope '{scope}'",
            )
        # 非表示運用はUI側で選択不可にする想定（DB側は is_visible だけ）
        # is_active=false のものをUIに混ぜるかは運用次第。混ぜたくないならここで弾く
        # if not d.is_active: ...

    # 既存を全消し→入れ直し（一括更新が簡単で安全）
    db.query(MstStatusUI).filter(MstStatusUI.scope == scope).delete()

    rows = []
    for x in items:
        row = MstStatusUI(
            scope=scope,
            status_key=x.status_key,
            display_order=x.display_order,
            is_visible=x.is_visible,
        )
        db.add(row)
        rows.append(row)

    db.commit()

    audit_logger.log(
        level=AuditLevel.INFO,
        action="UPSERT_STATUS_UI",
        target_type="mst_status_ui",
        target_id=scope,
        summary="Updated status UI order/visibility",
        detail={"count": len(items)},
    )

    # 再取得して整列返却
    out = (
        db.query(MstStatusUI)
        .filter(MstStatusUI.scope == scope)
        .order_by(MstStatusUI.display_order.asc(), MstStatusUI.status_key.asc())
        .all()
    )
    return out
