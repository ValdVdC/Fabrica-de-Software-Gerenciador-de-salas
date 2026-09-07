#!/bin/sh
set -e

crontab /etc/cron.d/sigaas-cron
chmod 0644 /etc/cron.d/sigaas-cron
touch /var/log/cron.log

echo "SIGAAS Cron Daemon iniciado com sucesso."
cron && tail -f /var/log/cron.log
