# --- stage 1 ---
FROM node:24.11.0-alpine3.22 AS builder

RUN apk update && apk upgrade

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

# RUN npm run lint
# RUN npm test -- run

RUN npm run build

# --- stage 2 ---
FROM nginx:1.27.0-alpine3.22

RUN apk update && apk upgrade

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]