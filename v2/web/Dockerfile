FROM node:20-slim

WORKDIR /app

COPY package.json tsconfig.json next.config.js ./
COPY app ./app
COPY lib ./lib

RUN npm install

EXPOSE 3010
CMD ["npm", "run", "dev"]


# # syntax=docker/dockerfile:1

# ##########
# # deps
# ##########
# FROM node:20-slim AS deps
# WORKDIR /app

# # 依存関係インストールに必要なファイルだけ先にコピー（キャッシュ効かせる）
# COPY package.json package-lock.json ./
# RUN npm ci

# ##########
# # build
# ##########
# FROM node:20-slim AS builder
# WORKDIR /app

# COPY --from=deps /app/node_modules ./node_modules
# COPY . .

# # Next.js build（package.json の build を呼ぶ）
# RUN npm run build

# ##########
# # runner
# ##########
# FROM node:20-slim AS runner
# WORKDIR /app
# ENV NODE_ENV=production

# # 非rootユーザー作成
# RUN useradd -m -u 10001 appuser

# # Next.js standalone を使う前提（next.config.js で output: 'standalone'）
# # もし standalone にしてない場合は下の「standaloneじゃない場合」を参照
# COPY --from=builder /app/public ./public
# COPY --from=builder /app/.next/static ./.next/static
# COPY --from=builder /app/.next/standalone ./

# # 権限調整
# RUN chown -R appuser:appuser /app
# USER appuser

# EXPOSE 3000

# # ヘルスチェック（/ が返る想定）
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#     CMD node -e "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# # standalone は server.js が生成される
# CMD ["node", "server.js"]
