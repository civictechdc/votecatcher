# Deployment Documentation

Production deployment guides for Votecatcher.

## Contents

| Document | Description |
|----------|-------------|
| [Docker Compose Deployment](./docker-compose-deployment.md) | Deploy with Docker Compose on a VPS |
| [Running Locally](../running-locally.md) | Local development setup |

## Quick Reference

For local development, see [Running Locally](../running-locally.md).

## Architecture

Production deployment uses Docker Compose with three services:

```
┌─────────────────────────────────────────┐
│  VPS (Ubuntu 22.04+, $5-20/mo)         │
│                                         │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Backend     │  │ Frontend        │  │
│  │ (FastAPI    │  │ (SvelteKit)     │  │
│  │  :8080)     │  │  :5173          │  │
│  └──────┬──────┘  └─────────────────┘  │
│         │                               │
│  ┌──────┴──────────────────────────┐   │
│  │ PostgreSQL (:5432)              │   │
│  │ Data volume: postgres_data      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Estimated Costs

| Provider | Instance Type | Est. Cost |
|----------|---------------|-----------|
| DigitalOcean | Basic Droplet | $6-12/mo |
| Linode | Shared CPU | $5-10/mo |
| Hetzner | Cloud VPS | $4-8/mo |
| AWS | t3.micro | $8-15/mo |
