# --- stage 1 ---
FROM node:24-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

# RUN npm run lint
# RUN npm test -- run

RUN npm run build

# --- stage 2 ---
FROM node:24-bookworm-slim

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist .

EXPOSE 3000

CMD ["serve", "-s", ".", "-l", "tcp://0.0.0.0:3000"]