#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

docker compose build api
docker compose up -d --no-deps api
docker compose ps api
