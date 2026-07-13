# ============================================================
# UnitForge — Dashboard (React + Vite)
# Multi-stage build:
#   Stage 1 (builder) — Node builds the static files
#   Stage 2 (runtime) — nginx serves the static files
# Final image is ~25MB instead of ~400MB
# ============================================================

# ---- Stage 1: Build ----------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (cached layer)
COPY package*.json .

# Install exact versions from package-lock.json
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ---- Stage 2: Runtime (nginx) ------------------------------
FROM nginx:alpine

# Copy built static files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config (handles React Router + API proxy)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
