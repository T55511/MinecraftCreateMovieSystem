# app/main.py

from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from .database import Base, engine, init_db # Baseとengineをインポート
from .api import endpoints as project_router # エンドポイントをインポート

# 💡 起動時に1回だけ初期化を実行
try:
    init_db()
except Exception as e:
    print(f"❌ DB Initialization failed: {e}")

app = FastAPI(
    title="動画制作効率化支援システム API",
    version="1.0.0"
)

# --- CORS 設定 ---
# TypeScriptのフロントエンドからのアクセスを許可するために必要
origins = [
    "http://localhost:3010",  # フロントエンドのポート (仮に3000番とする)
    "http://localhost:8010",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # すべてのメソッドを許可 (GET, POSTなど)
    allow_headers=["*"],
)

# --- ルートエンドポイント（動作確認用）---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Coding Partner API. System is running."}

# --- プロジェクトルーターを追加 ---
app.include_router(project_router.router)