# BlueOcean - Deploy em VPS com Docker

## Estrutura na VPS

```text
/opt/blueocean/
├── infra/
│   ├── docker-compose.yml
│   ├── .env
│   └── backup-postgres.sh
├── app/
│   ├── docker-compose.yml
│   ├── .env
│   └── codigo do projeto
└── backups/
```

## Preparacao inicial

```bash
sudo mkdir -p /opt/blueocean/{infra,app,backups}
cd /opt/blueocean/app
cp .env.example .env
./scripts/init-infra.sh
```

Na primeira execucao, o script cria `/opt/blueocean/infra/.env` e para. Edite os dois arquivos `.env`. A senha do Postgres em `/opt/blueocean/infra/.env` deve ser a mesma usada dentro de `DATABASE_URL` no `.env` da API.

Depois de editar os arquivos, execute novamente:

```bash
./scripts/init-infra.sh
```

Suba a API:

```bash
docker compose up -d --build
```

## Atualizacao da API

```bash
cd /opt/blueocean/app
git pull
./scripts/deploy-api.sh
```

O script de deploy nao chama `docker compose down`, nao usa `--volumes` e nao conhece o compose da infra.

## Backups

O servico `db-backup` gera arquivos `blueocean-*.sql.gz` em `/opt/blueocean/backups` e remove arquivos antigos conforme `BACKUP_RETENTION_DAYS`.

Para restaurar manualmente em uma manutencao planejada:

```bash
gzip -dc /opt/blueocean/backups/blueocean-YYYYMMDDTHHMMSSZ.sql.gz | docker exec -i blueocean_db psql -U blueocean -d blueocean
```
