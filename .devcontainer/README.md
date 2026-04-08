# VoteCatcher DevContainer

## Quick Start

1. Open this repository in VS Code
2. When prompted, click "Reopen in Container"
3. Wait for container to build (first time takes ~5 minutes)
4. Run the setup:
   ```bash
   .devcontainer/setup.sh
   ```

## Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
uv run main.py --env local
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bun run dev
```

## Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8080 | http://localhost:8080 |
| Backend Docs | 8080 | http://localhost:8080/docs |
| PostgreSQL | 5432 | localhost:5432 |

## Troubleshooting

### Container won't start
```bash
docker-compose down -v
docker-compose up --build
```

### Dependencies out of sync
```bash
.devcontainer/setup.sh
```
