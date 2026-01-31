from datetime import date
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine, get_db, SessionLocal, wait_for_db
from seed import seed_all
from models import TProjectTask, MCheckItem, MTaskCheckMap, TCheckResult

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

class TaskStatusPatch(BaseModel):
    status: str

class ChecklistItemOut(BaseModel):
    check_item_id: int
    label: str
    is_checked: bool

class ChecklistUpdateItem(BaseModel):
    check_item_id: int
    is_checked: bool
