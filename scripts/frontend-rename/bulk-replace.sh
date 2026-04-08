#!/usr/bin/env bash
# bulk-replace.sh — Replace frontend-svelt → frontend across file groups
# Usage: bash scripts/frontend-rename/bulk-replace.sh <commit-group>
#   commit-groups: ci, build, ide, security, docs, all
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

GROUP="${1:-all}"
FROM="frontend-svelt"
TO="frontend"

# Also handle the typo variant found in devcontainer
FROM2="frontend-svelte"

replace_in_file() {
	local file="$1"
	if [ -f "$file" ]; then
		sed -i '' "s|$FROM|$TO|g" "$file"
		sed -i '' "s|$FROM2|$TO|g" "$file"
		echo "  Updated: $file"
	else
		echo "  SKIP (not found): $file"
	fi
}

echo "=== Bulk Replace: $FROM → $TO (group: $GROUP) ==="

CI_FILES=(
	".github/workflows/ci.yml"
	".github/workflows/code-quality.yml"
	".github/workflows/security.yml"
	".github/workflows/benchmarks.yml"
	"justfile"
)

BUILD_FILES=(
	"docker-compose.yml"
	"docker-compose.supabase.yml"
	".pre-commit-config.yaml"
	"scripts/verify-fix-results.sh"
)

IDE_FILES=(
	".vscode/tasks.json"
	".vscode/launch.json"
	".zed/tasks.json"
	".zed/debug.json"
	".devcontainer/devcontainer.json"
	".devcontainer/docker-compose.override.yml"
	".devcontainer/setup.sh"
)

SECURITY_FILES=(
	".gitleaks.toml"
)

DOC_FILES=(
	"README.md"
	"docs/running-locally.md"
	"docs/development/README.md"
	"docs/user-guide.md"
	"docs/configuration-modes.md"
	"docs/demo-walkthrough.md"
	"docs/architecture/decisions/0005-dual-sse-architecture.md"
	"docs/architecture/c4-containers.md"
	"docs/architecture/c4-components.md"
	"docs/architecture/c4-context.md"
	"docs/deployment/README.md"
	"docs/deployment/docker-compose-deployment.md"
	"docs/DOCUMENTATION_STRATEGY.md"
	"docs/database/README.md"
	"docs/database/schema.md"
)

run_group() {
	local name="$1"
	shift
	local files=("$@")
	echo ""
	echo "--- $name ---"
	for f in "${files[@]}"; do
		replace_in_file "$f"
	done
}

case "$GROUP" in
ci)
	run_group "CI/CD + justfile" "${CI_FILES[@]}"
	;;
build)
	run_group "Build & Automation" "${BUILD_FILES[@]}"
	;;
ide)
	run_group "IDE & DevContainer" "${IDE_FILES[@]}"
	;;
security)
	run_group "Security Config" "${SECURITY_FILES[@]}"
	;;
docs)
	run_group "Documentation" "${DOC_FILES[@]}"
	find docs/ -name "*.md" -not -path "docs/qa/*" -exec grep -l "frontend-svelt" {} \; 2>/dev/null | while read -r f; do
		if ! echo "${DOC_FILES[@]}" | grep -q "$(basename "$f")"; then
			replace_in_file "$f"
		fi
	done
	;;
all)
	run_group "CI/CD + justfile" "${CI_FILES[@]}"
	run_group "Build & Automation" "${BUILD_FILES[@]}"
	run_group "IDE & DevContainer" "${IDE_FILES[@]}"
	run_group "Security Config" "${SECURITY_FILES[@]}"
	run_group "Documentation" "${DOC_FILES[@]}"
	find docs/ -name "*.md" -not -path "docs/qa/*" -exec grep -l "frontend-svelt" {} \; 2>/dev/null | while read -r f; do
		replace_in_file "$f"
	done
	;;
*)
	echo "Unknown group: $GROUP"
	echo "Usage: $0 {ci|build|ide|security|docs|all}"
	exit 1
	;;
esac

echo ""
echo "=== Bulk replace complete for group: $GROUP ==="
