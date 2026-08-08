# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build


# ── Stage 2: Final image ──────────────────────────────────────────────────────
FROM python:3.13-slim

# System deps: nginx + postgres build headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Backend ───────────────────────────────────────────────────────────────────
WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# ── Frontend static build ─────────────────────────────────────────────────────
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# ── Nginx config ──────────────────────────────────────────────────────────────
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# ── Startup script ────────────────────────────────────────────────────────────
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

CMD ["/start.sh"]
