# Multi-stage build для production

# Stage 1: Build
FROM node:18-alpine as build

WORKDIR /app

# Копирование package files
COPY package*.json ./
RUN npm ci

# Копирование исходников
COPY . .

# Build приложения
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/dist /usr/share/nginx/html

# Копирование nginx конфигурации
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
