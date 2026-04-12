#!/bin/bash
set -e

echo "=== Setting up VoteCatcher DevContainer ==="
echo "This setup uses justfile-first architecture"
echo ""

cd /workspace

echo "Checking prerequisites..."
if ! command -v just &>/dev/null; then
	echo "Installing just..."
	curl -fsSL https://pkg.mondoolabs.com/setup.sh | sudo bash
	sudo apt-get install -y just
fi

echo "Checking just installation..."
just --version

echo ""
echo "=== Running justfile-based setup ==="

echo "Installing all dependencies (backend + frontend)..."
just install

echo ""
echo "Installing CI/security tools..."
just install-tools

echo ""
echo "Installing pre-commit hooks..."
just install-hooks

echo ""
echo "Setting up environment files..."
if [ ! -f /workspace/backend/.env.local ]; then
	echo "Creating backend/.env.local..."
	cat >/workspace/backend/.env.local <<EOF
DATABASE_URL=postgresql://votecatcher:votecatcher_dev@db:5432/votecatcher
ENV=local
EOF
	echo "✓ Created backend/.env.local"
fi

if [ ! -f /workspace/frontend/.env.local ]; then
	echo "Creating frontend/.env.local..."
	cat >/workspace/frontend/.env.local <<EOF
VITE_API_URL=http://localhost:8080
DEMO_MODE=false
EOF
	echo "✓ Created frontend/.env.local"
fi

echo ""
echo "Running database migrations..."
just migrate

echo ""
echo "=== DevContainer Setup Complete ==="
echo ""
echo "Quick start commands:"
echo "  Backend:   just dev-backend"
echo "  Frontend:  just dev-frontend"
echo "  Database:  just dev-postgres"
echo "  Tests:     just test"
echo "  CI Sim:    just ci-sim"
echo ""
echo "See OPERATIONS.md for complete documentation"
