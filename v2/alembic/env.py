from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool # type: ignore

# Alembic Config
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 🔽 v2/api を import パスに追加
BASE_DIR = Path(__file__).resolve().parents[1]
API_DIR = BASE_DIR / "v2" / "api"
sys.path.append(str(API_DIR))

# 🔽 あなたの db.py / models.py を正しく読む
# trunk-ignore(ruff/E402)
from db import Base # type: ignore
# trunk-ignore(ruff/E402)
# trunk-ignore(ruff/F401)
import models # type: ignore # ★重要：models を import しないと metadata が空になる

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    DATABASE_URL は db.py と完全に同じルールにする
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@db:5432/app"
    )


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": get_database_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # 型変更も検知
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
