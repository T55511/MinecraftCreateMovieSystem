# Pythonベースイメージ
FROM python:3.11-slim

# 依存関係のインストールに必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係ファイルのコピー
COPY requirements.txt .

# Python依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . /app

# コンテナがリッスンするポート
EXPOSE 8010

# uvicornコマンドはdocker-compose.ymlで指定