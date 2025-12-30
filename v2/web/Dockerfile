FROM node:20-slim

WORKDIR /app

COPY package.json tsconfig.json next.config.js ./
COPY app ./app
COPY lib ./lib

RUN npm install

EXPOSE 3010
CMD ["npm", "run", "dev"]
