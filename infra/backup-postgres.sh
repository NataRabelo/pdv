#!/bin/sh
set -eu

: "${PGHOST:?PGHOST obrigatorio}"
: "${PGDATABASE:?PGDATABASE obrigatorio}"
: "${PGUSER:?PGUSER obrigatorio}"
: "${PGPASSWORD:?PGPASSWORD obrigatorio}"

interval="${BACKUP_INTERVAL_SECONDS:-86400}"
retention_days="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p /backups

while true; do
  timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
  target="/backups/blueocean-${timestamp}.sql.gz"

  echo "Iniciando backup do Postgres em ${target}"
  pg_dump --no-owner --no-privileges | gzip -9 > "${target}"
  echo "Backup concluido: ${target}"

  find /backups -type f -name "blueocean-*.sql.gz" -mtime +"${retention_days}" -delete
  sleep "${interval}"
done
