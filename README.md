# OceanBlue PDV

Sistema de PDV com:

- Controle de Estoque
- Controle Financeiro
- Multi-tenant
- Autenticação via JWT

## Rodar com Docker

```bash
cp .env.example .env
./scripts/init-infra.sh
docker compose up -d --build
```

## Deploy em Producao

Este projeto esta preparado para rodar em producao via Docker Compose com a API em Gunicorn, PostgreSQL em stack separada, porta da API publicada apenas em `127.0.0.1:5000` e logs enviados para stdout/stderr.

Na VPS, mantenha o banco em `/opt/blueocean/infra`, o codigo da API em `/opt/blueocean/app` e os dumps em `/opt/blueocean/backups`. O volume `blueocean_postgres_data` e a rede `blueocean_network` sao externos ao Compose.

Antes do deploy, copie `.env.example` para `.env`, preencha os segredos com valores fortes e mantenha `FLASK_ENV=production`. O acesso externo deve ser feito por um proxy reverso Nginx fora deste compose.

Use `scripts/init-infra.sh` somente na preparacao inicial da VPS ou em manutencoes planejadas. Na primeira execucao ele cria `/opt/blueocean/infra/.env` e para para voce preencher a senha do banco. Para atualizacoes diarias da API, use `scripts/deploy-api.sh`; ele nao executa comandos destrutivos no banco.
