# app/database.py

from pydoc import text
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from pydantic_settings import BaseSettings # type: ignore

# .envファイルから環境変数を読み込むための設定
class Settings(BaseSettings):
    database_url: str = "postgresql://myuser:mypassword@db:5432/minecraft_movie_db"

settings = Settings()

# 💡 エンジン、セッション、ベースは「1つだけ」定義する
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 依存性注入（DI）用の関数: リクエストごとに新しいDBセッションを提供
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 💡 追記: シーケンスをリセットする関数
def reset_task_template_sequence(engine):
    """
    m_task_template テーブルの ID シーケンスを、現在の最大 ID の次の値にリセットする。
    """
    with engine.connect() as connection:
        # SQLAchemy の text 関数を使用して生の SQL を実行
        # シーケンス名 'm_task_template_task_template_id_seq' は PostgreSQL の命名規則に基づいています
        sql_command = text("""
            SELECT setval('m_task_template_task_template_id_seq', 
                        (SELECT COALESCE(MAX(task_template_id), 1) FROM m_task_template), 
                        CASE WHEN (SELECT COALESCE(MAX(task_template_id), 0) FROM m_task_template) = 0 THEN FALSE ELSE TRUE END);
        """)
        connection.execute(sql_command)
        connection.commit()
    print("✅ m_task_template sequence successfully reset.")

def init_db():
    """DBが起動するのを待ってから初期化を実行する"""
    import app.models.project
    import app.models.master

    # 💡 接続リトライロジック
    max_retries = 5
    for i in range(max_retries):
        try:
            # 接続テスト
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as e:
            if i == max_retries - 1:
                raise e
            print(f"🔄 Database not ready yet... retrying ({i+1}/{max_retries})")
            time.sleep(3) # 3秒待機

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully.")
    
    try:
        reset_task_template_sequence(engine)
        print("✅ Sequences reset.")
    except Exception as e:
        print(f"⚠️ Sequence reset skipped (might be missing table): {e}")