#!/usr/bin/env bash
# changelog-summarize.sh — AI-powered changelog summarization
#
# Summarizes only the FIRST (latest) version section in the changelog.
# Older sections are preserved as-is.
#
# GUARDS (script exits early when any applies):
#   1. No git diff                   → nothing changed, skip
#   2. <10 lines added               → formatting-only change, skip
#   3. First section already summarized → preserve, skip
#   4. <MIN_COMMITS in latest version → small release, raw output sufficient, skip
#
# CONFIGURATION via environment variables (all optional):
#   CHANGELOG_FILE              Input/output file              (default: CHANGELOG.md)
#   CHANGELOG_PROMPT            System prompt file             (default: scripts/changelog-prompt.md)
#   CHANGELOG_MODEL             GitHub Models model ID         (default: deepseek/deepseek-v3-0324)
#   CHANGELOG_FALLBACK_MODEL    Fallback model on primary failure (default: openai/gpt-4.1-mini)
#   CHANGELOG_MIN_COMMITS       Skip threshold for bullet count (default: 6)
#   CHANGELOG_API_URL           API endpoint                   (default: https://models.github.ai/...)
#   CHANGELOG_DRY_RUN           Preview config without API call (default: false)
#
# AUTH: Uses GITHUB_TOKEN (CI) or gh auth token (local).
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
CHANGELOG_FILE="${CHANGELOG_FILE:-${1:-CHANGELOG.md}}"
PROMPT_FILE="${CHANGELOG_PROMPT:-${2:-scripts/changelog-prompt.md}}"
MODEL="${CHANGELOG_MODEL:-deepseek/deepseek-v3-0324}"
FALLBACK_MODEL="${CHANGELOG_FALLBACK_MODEL:-openai/gpt-4.1-mini}"
API_URL="${CHANGELOG_API_URL:-https://models.github.ai/inference/chat/completions}"
DRY_RUN="${CHANGELOG_DRY_RUN:-false}"
MIN_COMMITS="${CHANGELOG_MIN_COMMITS:-6}"

# ── Pre-flight checks ──────────────────────────────────────────
if [ ! -f "$CHANGELOG_FILE" ]; then
	echo "[ERROR] Changelog file not found: $CHANGELOG_FILE" >&2
	echo "        Run 'just changelog' first to generate raw output." >&2
	exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
	echo "[ERROR] Prompt file not found: $PROMPT_FILE" >&2
	echo "        This file should be tracked in git alongside this script." >&2
	exit 1
fi

FIRST_VERSION=$(grep -m1 '^## \[' "$CHANGELOG_FILE" || true)
if [ -z "$FIRST_VERSION" ]; then
	echo "[SKIP] No version sections found in $CHANGELOG_FILE."
	exit 0
fi

# ── Extract first section boundaries ───────────────────────────
FIRST_HEADER_LINE=$(grep -n "^## \[" "$CHANGELOG_FILE" | head -1 | cut -d: -f1)
SECOND_HEADER_LINE=$(grep -n "^## \[" "$CHANGELOG_FILE" | sed -n '2p' | cut -d: -f1)
TOTAL_LINES=$(wc -l <"$CHANGELOG_FILE")

if [ -n "$SECOND_HEADER_LINE" ]; then
	SECTION_END=$((SECOND_HEADER_LINE - 1))
else
	SECTION_END=$TOTAL_LINES
fi

FIRST_SECTION=$(sed -n "${FIRST_HEADER_LINE},${SECTION_END}p" "$CHANGELOG_FILE")
BULLET_COUNT=$(echo "$FIRST_SECTION" | grep -c '^-' || true)

# ── Guard 1: No diff at all ────────────────────────────────────
if git diff --quiet -- "$CHANGELOG_FILE" 2>/dev/null; then
	echo "[SKIP] No changes to $CHANGELOG_FILE — file matches last commit."
	exit 0
fi

# ── Guard 2: Trivial diff (formatting/header-only) ─────────────
DIFF_STATS=$(git diff --numstat -- "$CHANGELOG_FILE" 2>/dev/null || true)
if [ -n "$DIFF_STATS" ]; then
	ADD=$(echo "$DIFF_STATS" | awk '{print $1}')
	MATERIAL=${ADD:-0}
	if [ "$MATERIAL" -lt 10 ] 2>/dev/null; then
		echo "[SKIP] Only $MATERIAL lines added to changelog (threshold: 10)."
		echo "       Likely a formatting-only change — raw output preserved."
		exit 0
	fi
fi

# ── Guard 3: First section already summarized ──────────────────
# Compare only the first section against fresh git-cliff output for
# the same tag. If it already looks summarized (themed headings,
# narrative paragraphs), skip. Only raw bullet lists get summarized.
if command -v git-cliff &>/dev/null; then
	FIRST_TAG=$(echo "$FIRST_VERSION" | grep -oP '\[\K[^\]]+' | head -1)
	if [ -n "$FIRST_TAG" ]; then
		RAW_SECTION=$(git-cliff --config cliff.toml --tag "v${FIRST_TAG}" 2>/dev/null \
			| sed '/^# Changelog/d; /^<!-- generated/d' \
			| sed '/^$/N;/^\n$/d' \
			| sed -n '/^## \[/,/^## \[/p' \
			| head -n -1 \
			|| true)
		if [ -n "$RAW_SECTION" ]; then
			RAW_CLEAN=$(echo "$RAW_SECTION" | grep -v '^#' | grep -v '^$' | grep -v '<!--')
			FILE_CLEAN=$(echo "$FIRST_SECTION" | grep -v '^#' | grep -v '^$' | grep -v '<!--')
			if [ "$RAW_CLEAN" = "$FILE_CLEAN" ]; then
				echo "[INFO] First section matches raw git-cliff output — needs summarization."
			else
				MANUAL_DIFF=$(diff <(echo "$RAW_CLEAN") <(echo "$FILE_CLEAN") | grep -c '^[<>]' || true)
				if [ "$MANUAL_DIFF" -gt 5 ] 2>/dev/null; then
					echo "[SKIP] First section already summarized ($MANUAL_DIFF differences from raw)."
					exit 0
				fi
			fi
		fi
	fi
fi

# ── Guard 4: Small release ─────────────────────────────────────
if [ "$BULLET_COUNT" -lt "$MIN_COMMITS" ]; then
	echo "[SKIP] Latest version has $BULLET_COUNT commits (threshold: $MIN_COMMITS)."
	echo "       Raw git-cliff output is sufficient for small releases."
	echo "       Override: CHANGELOG_MIN_COMMITS=$BULLET_COUNT just changelog-summarize"
	exit 0
fi

# ── Prepare API request ────────────────────────────────────────
SYSTEM_PROMPT=$(cat "$PROMPT_FILE")

USER_MESSAGE="Transform this raw git-cliff changelog section into a Level 1 GitHub Release changelog following the rules above. Output ONLY the changelog section markdown (starting with ## [version]), no explanation, no file header.

---

$FIRST_SECTION"

# ── Dry run ────────────────────────────────────────────────────
if [ "$DRY_RUN" = "true" ]; then
	echo "=== DRY RUN — no API call will be made ==="
	echo ""
	echo "  Model:          $MODEL (fallback: $FALLBACK_MODEL)"
	echo "  API:            $API_URL"
	echo "  Latest bullets: $BULLET_COUNT (threshold: $MIN_COMMITS)"
	echo "  Changelog:      $TOTAL_LINES lines"
	echo "  Prompt:         $(wc -l <"$PROMPT_FILE" | tr -d ' ') lines"
	echo ""
	echo "All guards passed. Would proceed with summarization."
	exit 0
fi

# ── Authentication ─────────────────────────────────────────────
TOKEN=""
if [ -n "${GITHUB_TOKEN:-}" ]; then
	TOKEN="$GITHUB_TOKEN"
elif command -v gh &>/dev/null; then
	TOKEN=$(gh auth token 2>/dev/null || true)
fi

if [ -z "$TOKEN" ]; then
	echo "[ERROR] No authentication token found." >&2
	echo "        CI: ensure GITHUB_TOKEN is set (automatic in GitHub Actions)." >&2
	echo "        Local: run 'gh auth login' or set GITHUB_TOKEN env var." >&2
	exit 1
fi

# ── Call GitHub Models API with fallback ───────────────────────
MODELS=("$MODEL" "$FALLBACK_MODEL")
CONTENT=""

for TRY_MODEL in "${MODELS[@]}"; do
	echo "[INFO] Summarizing $BULLET_COUNT commits with $TRY_MODEL..."

	RESPONSE=$(curl -s -X POST "$API_URL" \
		-H "Authorization: Bearer $TOKEN" \
		-H "Content-Type: application/json" \
		-H "Accept: application/vnd.github+json" \
		-d "$(
			jq -n \
				--arg model "$TRY_MODEL" \
				--arg system "$SYSTEM_PROMPT" \
				--arg user "$USER_MESSAGE" \
				'{
                model: $model,
                messages: [
                    {role: "system", content: $system},
                    {role: "user", content: $user}
                ],
                temperature: 0.3,
                max_tokens: 4000
            }'
		)")

	CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')

	if [ -n "$CONTENT" ]; then
		MODEL="$TRY_MODEL"
		break
	fi

	ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // "unknown"' 2>/dev/null)
	echo "[WARN] $TRY_MODEL returned no content ($ERROR_MSG). Trying next model..."
done

# ── Error handling ─────────────────────────────────────────────
if [ -z "$CONTENT" ]; then
	echo "[WARN] All models failed. Keeping raw git-cliff output."
	exit 0
fi

# ── Write output ───────────────────────────────────────────────
FOOTER="\n<!-- generated by git-cliff, summarized by GitHub Models ($MODEL) -->\n<!-- Format: https://keepachangelog.com/en/1.0.0/ -->"

NEW_SECTION=$(echo "$CONTENT" | sed '/^# Changelog/d' | sed '/^<!--/d' | sed '/^$/N;/^\n$/d')

if [ -n "$SECOND_HEADER_LINE" ]; then
	REST=$(sed -n "$((SECOND_HEADER_LINE)),\$p" "$CHANGELOG_FILE")
else
	REST=""
fi

{
	printf "# Changelog\n\n"
	echo "$NEW_SECTION"
	echo ""
	if [ -n "$REST" ]; then
		echo "$REST"
	fi
	printf "%b" "$FOOTER"
	echo ""
} >"$CHANGELOG_FILE"

OUTPUT_LINES=$(wc -l <"$CHANGELOG_FILE" | tr -d ' ')
OUTPUT_THEMES=$(grep -c '^### ' "$CHANGELOG_FILE" || echo 0)
echo "[OK] Summarized changelog written to $CHANGELOG_FILE"
echo "     Input: $BULLET_COUNT bullets → Output: $OUTPUT_LINES lines, $OUTPUT_THEMES themes (model: $MODEL)"
