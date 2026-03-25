FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# DB-Migration beim Container-Start (nicht Build), damit sie auf das persistente Volume schreibt
CMD ["sh", "-c", "python -c 'from app.database import init_db; init_db()' && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
