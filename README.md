# OceanBlue PDV

Sistema de PDV com:

- Controle de Estoque
- Controle Financeiro
- Multi-tenant
- Autenticação via JWT

## Rodar com Docker

```bash
docker-compose up --build
```

## Deploy em Producao

Este projeto esta preparado para rodar em producao via Docker Compose com a API em Gunicorn, PostgreSQL em container dedicado, porta da API publicada apenas em `127.0.0.1:5000` e logs enviados para stdout/stderr.

Antes do deploy, copie `.env.example` para `.env`, preencha os segredos com valores fortes e mantenha `FLASK_ENV=production`. O acesso externo deve ser feito por um proxy reverso Nginx fora deste compose.

O passo a passo completo do deploy deve ficar documentado em `deploy-blueocean-guia.md`.
