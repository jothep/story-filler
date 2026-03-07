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

# Install latest serve version and clean cache to get updated dependencies
RUN npm cache clean --force && npm install -g serve@latest

COPY --from=builder /app/dist/ .

EXPOSE 3000

CMD ["serve", "-s", ".", "-l", "tcp://0.0.0.0:3000"]