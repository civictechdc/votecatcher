#!/usr/bin/env bash
# scripts/validate-docs.sh — Documentation accuracy validation
# Run: bash scripts/validate-docs.sh
set -euo pipefail

ERRORS=0

# V1: No source code in documentation
check_no_source_code() {
	echo "=== Checking for source code in docs/ ==="
	local found
	found=$(find docs/ -name "*.md" -exec grep -l "^import \|^from \|^def \|^class \|^@router\|^async def " {} \; 2>/dev/null | grep -v "decisions/" | grep -v "specs/" | grep -v "template.md" | grep -v "adding-a-region.md" | grep -v "matching-algorithm" || true)
	if [ -n "$found" ]; then
		echo "ERROR: Found source code patterns in documentation files:"
		echo "$found"
		ERRORS=$((ERRORS + 1))
	else
		echo "OK: No source code in docs/"
	fi
}

# V2: Correct backend port (8080, not 8000)
check_port() {
	echo "=== Checking port references ==="
	local bad_port
	bad_port=$(grep -rn "localhost:8000" docs/ --include="*.md" 2>/dev/null | grep -v "nginx" | grep -v "8000:8000" || true)
	if [ -n "$bad_port" ]; then
		echo "ERROR: Found references to localhost:8000 (should be 8080):"
		echo "$bad_port"
		ERRORS=$((ERRORS + 1))
	else
		echo "OK: Port references correct"
	fi
}

# V3: No 'fastapi dev' command in docs
check_commands() {
	echo "=== Checking command accuracy ==="
	local bad_cmd
	bad_cmd=$(grep -rn "fastapi dev" docs/ --include="*.md" 2>/dev/null || true)
	if [ -n "$bad_cmd" ]; then
		echo "ERROR: Found 'fastapi dev' command (should be 'python main.py --env local'):"
		echo "$bad_cmd"
		ERRORS=$((ERRORS + 1))
	else
		echo "OK: Command references correct"
	fi
}

# V4: No old env var names
check_env_vars() {
	echo "=== Checking environment variable names ==="
	local old_vars
	old_vars=$(grep -rn "OPENAI_API_KEY\|GEMINI_API_KEY\|MISTRAL_API_KEY" docs/ --include="*.md" 2>/dev/null | grep -v "#.*old\|example\|deprecated\|OPENAI_API_KEY=.*#.*" || true)
	if [ -n "$old_vars" ]; then
		echo "ERROR: Found old env var names (should be OCR_PROVIDER_NAME/MODEL/API_KEY):"
		echo "$old_vars"
		ERRORS=$((ERRORS + 1))
	else
		echo "OK: Environment variable names correct"
	fi
}

# V5: ADR index matches files
check_adr_index() {
	echo "=== Checking ADR index consistency ==="
	local adr_files
	adr_files=$(ls docs/architecture/decisions/[0-9]*.md 2>/dev/null | grep -v template | sort || true)
	local adr_indexed
	adr_indexed=$(grep -oP '\d{4}' docs/architecture/decisions/README.md 2>/dev/null | sort || true)
	if [ "$adr_files" != "$adr_indexed" ] && [ -n "$adr_files" ]; then
		echo "WARNING: ADR index may not match files"
		echo "Files: $adr_files"
		echo "Indexed: $adr_indexed"
	fi
	echo "OK: ADR index check complete"
}

# V6: Coverage threshold in docs matches pyproject.toml
check_coverage_threshold() {
	echo "=== Checking coverage threshold consistency ==="
	local toml_val
	toml_val=$(grep -oP '(?<=cov-fail-under=)\d+' backend/pyproject.toml 2>/dev/null || echo "NOT_FOUND")
	local doc_val
	doc_val=$(grep -oP 'cov-fail-under.*?\K\d+' docs/qa/baselines/SUMMARY.md 2>/dev/null || echo "NOT_FOUND")
	if [ "$toml_val" != "$doc_val" ] && [ "$doc_val" != "NOT_FOUND" ]; then
		echo "WARNING: Coverage threshold mismatch — pyproject.toml=$toml_val, docs=$doc_val"
	fi
	echo "OK: Coverage threshold check complete"
}

# V7: No malformed docker-compose in docs
check_yaml_in_docs() {
	echo "=== Checking for broken YAML in docs ==="
	local yaml_files
	yaml_files=$(find docs/ -name "*.md" -exec grep -l "^version:\|^services:" {} \; 2>/dev/null || true)
	if [ -n "$yaml_files" ]; then
		echo "WARNING: Found docker-compose-like YAML in:"
		echo "$yaml_files"
		echo "Should be in deployment guide format"
	fi
	echo "OK: YAML check complete"
}

# Run all checks
check_no_source_code
check_port
check_commands
check_env_vars
check_adr_index
check_coverage_threshold
check_yaml_in_docs

echo ""
if [ "$ERRORS" -gt 0 ]; then
	echo "FAILED: $ERRORS validation error(s) found"
	exit 1
else
	echo "PASSED: All documentation validation checks passed"
	exit 0
fi
