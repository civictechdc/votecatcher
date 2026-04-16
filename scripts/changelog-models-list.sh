#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-.agent-workspace/changelog-samples/benchmarks/free-models.json}"

TOKEN=""
if [ -n "${GITHUB_TOKEN:-}" ]; then
	TOKEN="$GITHUB_TOKEN"
elif command -v gh &>/dev/null; then
	TOKEN=$(gh auth token 2>/dev/null || true)
fi

if [ -z "$TOKEN" ]; then
	echo "ERROR: No auth token. Set GITHUB_TOKEN or run 'gh auth login'." >&2
	exit 1
fi

echo "Fetching GitHub Models catalog..."

CATALOG=$(curl -s "https://models.github.ai/catalog/models" \
	-H "Authorization: Bearer $TOKEN" \
	-H "Accept: application/vnd.github+json")

echo "$CATALOG" | jq '[.[] | select(
    .rate_limit_tier == "low" or .rate_limit_tier == "high"
) | select(
    (.supported_output_modalities // []) | contains(["text"])
) | select(
    (.capabilities // []) | contains(["streaming"])
) | {
    id,
    name,
    publisher,
    tier: .rate_limit_tier,
    max_input_tokens: .limits.max_input_tokens,
    max_output_tokens: .limits.max_output_tokens,
    url: .html_url
}] | sort_by([.tier, .publisher, .name])' >"$OUTPUT"

COUNT=$(jq 'length' "$OUTPUT")
LOW=$(jq '[.[] | select(.tier == "low")] | length' "$OUTPUT")
HIGH=$(jq '[.[] | select(.tier == "high")] | length' "$OUTPUT")

echo "Saved $COUNT models to $OUTPUT ($LOW low-tier, $HIGH high-tier)"
echo ""
echo "Low-tier models (15 req/min, 150 req/day):"
jq -r '.[] | select(.tier == "low") | "  \(.id)"' "$OUTPUT"
echo ""
echo "High-tier models (10 req/min, 50 req/day):"
jq -r '.[] | select(.tier == "high") | "  \(.id)"' "$OUTPUT"
