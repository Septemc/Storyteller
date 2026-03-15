FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend_vue

COPY frontend_vue/package*.json ./
RUN npm ci

COPY frontend_vue/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend/ ./backend
COPY frontend/ ./frontend
COPY frontend_vue/ ./frontend_vue
COPY scripts/ ./scripts
COPY README.md ./
COPY --from=frontend-builder /app/frontend_vue/dist ./frontend_vue/dist

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/', timeout=3)"

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8010"]
