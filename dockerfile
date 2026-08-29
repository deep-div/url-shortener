# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build


# ── Stage 2: Final image ──────────────────────────────────────────────────────
# Base off Kong's official Docker image (Ubuntu-based, Kong pre-installed and
# verified to work) instead of installing Kong via a manually-configured apt
# repo — avoids brittle GPG key / repo URL issues.
FROM kong:3.9-ubuntu

USER root

# System deps: nginx (static file server) + Python + postgres build headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    libpq-dev \
    gcc \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Kong runtime config — DB-less (declarative), listens on 0.0.0.0:80,
# Admin API restricted to localhost only.
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/etc/kong/kong.yml
ENV KONG_PROXY_LISTEN=0.0.0.0:80
ENV KONG_ADMIN_LISTEN=127.0.0.1:8001
ENV KONG_NGINX_DAEMON=off
ENV KONG_NGINX_WORKER_PROCESSES=1
ENV KONG_LOG_LEVEL=warn
ENV KONG_PROXY_ACCESS_LOG=off
ENV KONG_PROXY_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_ACCESS_LOG=/dev/stdout
ENV KONG_ADMIN_ERROR_LOG=/dev/stderr

# ── Backend ───────────────────────────────────────────────────────────────────
WORKDIR /app/backend

# Isolated virtualenv — Ubuntu 24.04 (used by the kong:3.9-ubuntu image)
# blocks system-wide pip installs (PEP 668), so we use a venv instead.
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# ── Frontend static build ─────────────────────────────────────────────────────
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# ── Nginx config (static frontend server only, internal port 3000) ───────────
COPY gateway/nginx/default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# ── Kong config (declarative routing) ─────────────────────────────────────────
COPY gateway/kong/kong.yml /etc/kong/kong.yml

# ── Startup script ────────────────────────────────────────────────────────────
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

# Override the base Kong image's entrypoint — we manage process startup
# ourselves via start.sh (backend + nginx + kong all in one script).
ENTRYPOINT []
CMD ["/start.sh"]
