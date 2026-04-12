#!/usr/bin/env bash
set -euo pipefail

echo "=== VoteCatcher Setup ==="

if ! command -v docker &>/dev/null; then
	echo "Error: Docker is not installed."
	echo "Install it from https://www.docker.com/products/docker-desktop/"
	exit 1
fi

if ! docker info &>/dev/null; then
	echo "Error: Docker is not running. Please open Docker Desktop first."
	exit 1
fi

if [ ! -f backend/.env.local ]; then
	cp backend/.env.example backend/.env.local
	echo "Created backend/.env.local"
fi

if [ ! -f frontend/.env ]; then
	cp frontend/.env.example frontend/.env
	echo "Created frontend/.env"
fi

echo "Starting VoteCatcher..."
echo "  App:  http://localhost:5173"
echo "  API:  http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop."
echo ""

docker compose up --build
