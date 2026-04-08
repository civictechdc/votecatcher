# Docker Compose Deployment Guide

Deploy Votecatcher on a VPS using Docker Compose. This is the recommended approach for production.

## Architecture

```
┌─────────────────────────────────────────┐
│  VPS (Ubuntu 22.04+)                    │
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

Three containers: backend (FastAPI on port 8080), frontend (SvelteKit on port 5173), and PostgreSQL 16.

## Prerequisites

- VPS running Ubuntu 22.04+ (or similar Linux)
- Docker and Docker Compose v2+
- At least 1GB RAM, 1 CPU core
- An OCR provider API key (e.g., OpenAI)

### Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Log out and back in for the group change to take effect.

## Quick Start

### 1. Clone and Configure

```bash
git clone <your-repo-url> votecatcher
cd votecatcher
```

### 2. Set Environment Variables

Copy the example env file and configure it:

```bash
cp backend/.env.example backend/.env.local
```

Edit `backend/.env.local` — at minimum set:

```env
DATABASE_URL=postgresql+psycopg://votecatcher:votecatcher_dev@db:5432/votecatcher  # pragma: allowlist secret
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=sk-your-key-here  # pragma: allowlist secret
```

### 3. Start Services

```bash
docker compose up -d --build
```

### 4. Verify

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{"status": "healthy"}
```

Access the frontend at `http://your-vps-ip:5173`.

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://votecatcher:votecatcher_dev@db:5432/votecatcher` | <!-- pragma: allowlist secret -->
| `OCR_PROVIDER_NAME` | OCR provider to use | `open_ai` |
| `OCR_PROVIDER_MODEL` | OCR model to use | `gpt-4o-mini` |
| `OCR_PROVIDER_API_KEY` | API key for the OCR provider | `sk-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `FEATURE_ENABLE_SIMULATION` | Enable simulation mode (no OCR calls) | `0` |
| `FEATURE_ENABLE_BETA_FEATURES` | Enable beta features | `0` |
| `FEATURE_ENABLE_DEBUG_MODE` | Enable debug mode | `0` |
| `FEATURE_DEMO_MODE` | Enable demo mode | `0` |

### Supabase (Optional)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_REGION=aws-0-us-east-1
```

## Managing Services

### View Logs

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop Services

```bash
docker compose down
```

Data is preserved in the `postgres_data` Docker volume.

### Update to Latest Version

```bash
git pull origin main
docker compose up -d --build
```

### Restart a Single Service

```bash
docker compose restart backend
docker compose restart frontend
```

## Backup and Restore

### Backup the Database

```bash
docker compose exec db pg_dump -U votecatcher votecatcher > backup.sql
```

### Restore the Database

```bash
cat backup.sql | docker compose exec -T db psql -U votecatcher votecatcher
```

### Backup the Entire Data Volume

```bash
docker run --rm -v votecatcher_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data.tar.gz -C /data .
```

## TLS/HTTPS (Production)

Docker Compose does not include a reverse proxy. For production TLS, add one of:

### Option A: Caddy (Recommended — automatic HTTPS)

```bash
# Install Caddy
sudo apt install caddy

# /etc/caddy/Caddyfile
your-domain.com {
    reverse_proxy localhost:5173
}

api.your-domain.com {
    reverse_proxy localhost:8080
}
```

### Option B: Nginx + Certbot

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

```nginx
# /etc/nginx/sites-available/votecatcher
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then run `sudo certbot --nginx -d your-domain.com`.

## Resource Requirements

| Component | RAM | Disk |
|-----------|-----|------|
| Backend | ~200MB | ~500MB |
| Frontend | ~100MB | ~200MB |
| PostgreSQL | ~200MB | ~1GB (grows with data) |
| **Total** | **~500MB** | **~2GB** |

## Estimated Monthly Costs

| Provider | Instance Type | Est. Cost |
|----------|---------------|-----------|
| DigitalOcean | Basic Droplet (1GB) | $6-12/mo |
| Linode | Shared CPU (1GB) | $5-10/mo |
| Hetzner | Cloud VPS (CX22) | $4-8/mo |
| AWS | t3.micro | $8-15/mo |

## Troubleshooting

### Backend won't start

```bash
docker compose logs backend
```

Common issues:
- Missing `OCR_PROVIDER_API_KEY` in `.env.local`
- Wrong `DATABASE_URL` format (must use `db` as hostname, not `localhost`)
- Port 8080 already in use: `sudo lsof -i :8080`

### Database connection errors

Ensure the backend `DATABASE_URL` uses `db` as the hostname (the Docker service name):

```env
DATABASE_URL=postgresql+psycopg://votecatcher:votecatcher_dev@db:5432/votecatcher  # pragma: allowlist secret
```

### Frontend can't reach backend

Check that `VITE_API_URL` is set correctly in `docker-compose.yml`:

```yaml
environment:
  - VITE_API_URL=http://localhost:8080
```

For production, set this to your backend's public URL.

## Related Documentation

- [Running Locally](../running-locally.md) — local development setup
- [Architecture](../architecture/README.md) — system architecture diagrams
- [User Guide](../user-guide.md) — application usage guide
