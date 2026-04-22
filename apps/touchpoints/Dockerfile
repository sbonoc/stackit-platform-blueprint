# syntax=docker/dockerfile:1
# --- builder -----------------------------------------------------------
FROM node:24.8.0-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

# --- runtime -----------------------------------------------------------
FROM nginx:1.29.2-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
