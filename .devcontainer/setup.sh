#!/bin/bash
set -e

echo "=== Setting up VoteCatcher DevContainer ==="
echo "This setup uses justfile-first architecture"
echo ""

cd /workspace

GIT_MIN_VERSION="2.54"
GIT_VERSION=$(git --version | grep -oP '\d+\.\d+.\d+' | head -1)
GIT_MAJOR=$(echo "$GIT_VERSION" | cut -d. -f1)
GIT_MINOR=$(echo "$GIT_VERSION" | cut -d. -f2)
GIT_REQ_MAJOR=$(echo "$GIT_MIN_VERSION" | cut -d. -f1)
GIT_REQ_MINOR=$(echo "$GIT_MIN_VERSION" | cut -d. -f1-2 | cut -d. -f2)
if [ "$GIT_MAJOR" -lt "$GIT_REQ_MAJOR" ] || { [ "$GIT_MAJOR" -eq "$GIT_REQ_MAJOR" ] && [ "$GIT_MINOR" -lt "$GIT_REQ_MINOR" ]; }; then
	echo "ERROR: git >= ${GIT_MIN_VERSION} required (found ${GIT_VERSION}) for pre-commit maintenance configs"
	exit 1
fi
echo "✓ git ${GIT_VERSION} >= ${GIT_MIN_VERSION}"

if ! command -v just &>/dev/null; then
	echo "Installing just..."
	JUST_VERSION="1.40.0"
	curl -fsSL "https://github.com/casey/just/releases/download/${JUST_VERSION}/just-${JUST_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
		| sudo tar xz -C /usr/local/bin just
	echo "✓ just v${JUST_VERSION} installed"
fi

echo "Checking just installation..."
just --version

echo "Installing osv-scanner..."
if ! command -v osv-scanner &>/dev/null; then
	OSV_VERSION="1.9.2"
	curl -fsSL "https://github.com/google/osv-scanner/releases/download/v${OSV_VERSION}/osv-scanner_linux_amd64" \
		-o /usr/local/bin/osv-scanner
	sudo chmod +x /usr/local/bin/osv-scanner
	echo "✓ osv-scanner v${OSV_VERSION} installed"
else
	echo "✓ osv-scanner already installed"
fi

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
