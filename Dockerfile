# Stage 1: CSS-Build mit Node (nur Build-Zeit, nicht im finalen Image)
FROM node:20-alpine AS css-builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY tailwind.config.js ./
COPY static/css/input.css ./static/css/input.css
COPY templates ./templates
COPY app ./app
RUN npx tailwindcss -i ./static/css/input.css -o ./static/css/app.css --minify

# Stage 2: Python-Runtime
FROM python:3.13-slim
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
COPY --from=css-builder /build/static/css/app.css ./static/css/app.css

EXPOSE 8000

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# DB-Migration beim Container-Start (nicht Build), damit sie auf das persistente Volume schreibt
# --proxy-headers / --forwarded-allow-ips='*': hinter Fly-Proxy nötig, damit uvicorn
# X-Forwarded-Proto auswertet. Sonst baut Starlettes url_for()/307-Redirects absolute
# http://-URLs → Mixed Content blockt CSS, /admin redirected auf http.
CMD ["sh", "-c", "python -c 'from app.database import init_db; init_db()' && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"]
