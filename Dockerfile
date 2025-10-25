# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN useradd -m -u 1001 appuser
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl         && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=8080
USER appuser
EXPOSE 8080

CMD ["gunicorn", "wsgi:app", "-c", "gunicorn.conf.py"]
