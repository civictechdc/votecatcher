#!/bin/bash
set -e

echo "=== Setting up VoteCatcher DevContainer ==="

echo "Setting up backend..."
cd /workspace/backend
uv sync --dev

echo "Setting up frontend..."
cd /workspace/frontend-svelt
bun install

if [ ! -f /workspace/backend/.env.local ]; then
	echo "Creating .env.local template..."
	cat >/workspace/backend/.env.local <<EOF
DATABASE_URL=postgresql://votecatcher:votecatcher_dev@db:5432/votecatcher
VITE_API_URL=http://localhost:8080
EOF
fi

echo "=== Setup complete ==="
echo "Run 'bun run dev' in frontend-svelt/ and 'uv run main.py --env local' in backend/"
