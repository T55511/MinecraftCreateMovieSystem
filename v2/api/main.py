from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine, SessionLocal, wait_for_db
from seed import seed_all

from routes import router

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
