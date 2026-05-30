FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PORT=7860
ENV DATABASE_URL=sqlite:////data/ohmatt.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data

COPY requirements_fastapi.txt .
RUN pip install --no-cache-dir -r requirements_fastapi.txt

COPY app ./app
COPY run.py .

EXPOSE 7860

CMD ["sh", "-c", "gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-7860} --workers 1 --timeout 120"]
