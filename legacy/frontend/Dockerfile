FROM node:20-alpine

WORKDIR /app

# 依存関係をコピーしてインストール
COPY package*.json ./
RUN npm install

# アプリケーションコードをコピー
COPY . .

# 💡 明示的に環境変数を固定
ENV NODE_ENV=development
ENV HOST=0.0.0.0
ENV PORT=3000

# ポート3000を開放（docker-composeの右側と一致させる）
EXPOSE 3000

# 開発用サーバーを起動
CMD ["npm", "run", "dev"]