# --- stage 1 ---
FROM node:24.10.0-alpine3.21 AS builder

RUN apk update && apk upgrade

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

# RUN npm run lint
# RUN npm test -- run

RUN npm run build

# --- stage 2 ---
FROM node:24.10.0-alpine3.21

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist .

EXPOSE 3000

CMD ["serve", "-s", ".", "-l", "3000"]