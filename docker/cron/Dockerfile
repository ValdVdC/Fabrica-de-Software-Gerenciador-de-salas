FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app
COPY docker/cron/crontab /etc/cron.d/sigaas-cron
COPY docker/cron/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && chmod 0644 /etc/cron.d/sigaas-cron

ENTRYPOINT ["/entrypoint.sh"]
