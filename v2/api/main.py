from fastapi import FastAPI, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi.exceptions import RequestValidationError # type: ignore
from core.audit_log import audit_logger, AuditLevel, EventType, AUDIT_LOG_PATH  # パスはあなたの構成に合わせて

import uuid
import traceback
from db import Base, engine, SessionLocal, wait_for_db
from seed import seed_all

from routes import router
from services.event_log_writer import start_writer
import os
from pathlib import Path
from sqlalchemy import text # type: ignore

app = FastAPI(title="Minecraft Create Movie System v2 API")

app.include_router(router)

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

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    audit_logger.log(
        level=AuditLevel.INFO,
        event_type=EventType.VALIDATION,
        request_id=getattr(request.state, "request_id", None),
        action=f"{request.method} {request.url.path}",
        target_type="validation_error",
        target_id=None,
        summary="Request validation error",
        detail={"errors": exc.errors()},
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    audit_logger.log(
        level=AuditLevel.ERROR,
        event_type=EventType.ERROR,
        request_id=getattr(request.state, "request_id", None),
        action=f"{request.method} {request.url.path}",
        target_type="unhandled_exception",
        target_id=None,
        summary=str(exc),
        detail={"traceback": traceback.format_exc()},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.on_event("startup")
# trunk-ignore(ruff/F811)
def on_startup():
    if os.getenv("RESET_LOGS", "0") == "1":
        # DBログ削除
        db = SessionLocal()
        try:
            db.execute(text("TRUNCATE TABLE t_event_log"))
            db.commit()
        finally:
            db.close()

        # ファイルログ削除（空にする）
        Path(AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(AUDIT_LOG_PATH).write_text("", encoding="utf-8")
    start_writer()