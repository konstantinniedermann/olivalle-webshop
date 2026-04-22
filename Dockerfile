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

# Litestream-Binary installieren (pinned, analog zum SHA-Pinning-Grundsatz).
# Architektur via TARGETARCH damit fly sowohl amd64 als auch arm64 deployen kann.
ARG LITESTREAM_VERSION=0.3.13
ARG TARGETARCH=amd64
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSL "https://github.com/benbjohnson/litestream/releases/download/v${LITESTREAM_VERSION}/litestream-v${LITESTREAM_VERSION}-linux-${TARGETARCH}.tar.gz" \
      | tar -xzC /usr/local/bin \
 && apt-get purge -y curl \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

COPY litestream.yml /etc/litestream.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Migrationen + uvicorn werden von entrypoint.sh orchestriert.
ENTRYPOINT ["/entrypoint.sh"]
