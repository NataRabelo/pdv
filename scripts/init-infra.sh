#!/bin/sh
set -eu

app_dir="$(cd "$(dirname "$0")/.." && pwd)"
base_dir="$(cd "${app_dir}/.." && pwd)"
infra_dir="${base_dir}/infra"
backups_dir="${base_dir}/backups"

docker network create blueocean_network 2>/dev/null || true
docker volume create blueocean_postgres_data >/dev/null
mkdir -p "${infra_dir}" "${backups_dir}"

if [ ! -f "${infra_dir}/docker-compose.yml" ]; then
  cp "${app_dir}/infra/docker-compose.yml" "${infra_dir}/docker-compose.yml"
fi

if [ ! -f "${infra_dir}/backup-postgres.sh" ]; then
  cp "${app_dir}/infra/backup-postgres.sh" "${infra_dir}/backup-postgres.sh"
fi

if [ ! -f "${infra_dir}/.env" ]; then
  cp "${app_dir}/infra/.env.example" "${infra_dir}/.env"
  echo "Edite ${infra_dir}/.env antes de subir a infra novamente."
  exit 1
fi

docker compose --env-file "${infra_dir}/.env" -f "${infra_dir}/docker-compose.yml" up -d
docker compose --env-file "${infra_dir}/.env" -f "${infra_dir}/docker-compose.yml" ps
