#!/bin/bash
set -euo pipefail

# Safe v1/v2 local comparison harness.
# Runs the same queries against two explicit scripts and stores JSON outputs locally.

if [ $# -lt 2 ]; then
  echo "Usage: bash scripts/test-v1-vs-v2.sh <baseline-script> <candidate-script>"
  exit 1
fi

BASELINE_SCRIPT="$1"
CANDIDATE_SCRIPT="$2"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_DIR="$REPO_DIR/.last30days-compare/v1-vs-v2-${TIMESTAMP}"
V1_DIR="$OUT_DIR/v1"
V2_DIR="$OUT_DIR/v2"

mkdir -p "$V1_DIR" "$V2_DIR"

echo "📁 Output directory: $OUT_DIR"
echo ""

QUERIES=(
  "prompting techniques for chatgpt for legal questions"
  "best clawdbot use cases"
  "how to best setup clawdbot"
  "prompting tips for nano banana pro for ios designs"
  "top claude code skills"
  "using ChatGPT to make images of dogs"
  "research best practices for beautiful remotion animation videos in claude code"
  "photorealistic people in nano banana pro"
  "What are the best rap songs lately"
  "what are people saying about DeepSeek R1"
  "best practices for cursor rules files for Cursor"
  "prompt advice for using suno to make killer songs in simple mode"
  "how do I use Codex with Claude Code on same app to make it better"
  "kanye west"
  "howie.ai"
  "open claw"
  "nano banana pro prompting"
)

TYPES=(
  "PROMPTING+TOOL"
  "RECOMMENDATIONS"
  "HOW-TO"
  "PROMPTING+TOOL"
  "RECOMMENDATIONS"
  "GENERAL"
  "PROMPTING"
  "PROMPTING"
  "RECOMMENDATIONS"
  "NEWS"
  "PROMPTING"
  "PROMPTING"
  "HOW-TO"
  "NEWS"
  "GENERAL"
  "GENERAL"
  "PROMPTING"
)

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-50
}

run_version() {
  local version="$1"
  local outdir="$2"
  local script_path="$3"
  local total=${#QUERIES[@]}

  echo ""
  echo "=========================================="
  echo "  Running $version — $total queries"
  echo "=========================================="
  echo ""

  for i in "${!QUERIES[@]}"; do
    local query="${QUERIES[$i]}"
    local type="${TYPES[$i]}"
    local slug
    slug=$(slugify "$query")
    local num=$((i + 1))
    local outfile="$outdir/${num}-${slug}.txt"
    local errfile="$outdir/${num}-${slug}.stderr.txt"

    echo "[$version] ($num/$total) $query [$type]"

    local start_time
    start_time=$(date +%s)

    if /usr/local/python3.12/bin/python3.12 "$script_path" \
      "$query" --emit=json --quick \
      > "$outfile" 2>"$errfile"; then
      local end_time
      end_time=$(date +%s)
      local duration=$((end_time - start_time))
      local lines
      lines=$(wc -l < "$outfile")
      echo "  ✅ Done — ${lines} lines, ${duration}s"
    else
      local exit_code=$?
      echo "  ❌ Failed (exit $exit_code)" | tee -a "$outfile"
    fi

    # Brief pause between queries to avoid rate limits
    sleep 3
  done
}

run_version "V1" "$V1_DIR" "$BASELINE_SCRIPT"
run_version "V2" "$V2_DIR" "$CANDIDATE_SCRIPT"

# === Phase 3: Generate summary ===
echo ""
echo "=========================================="
echo "  Generating comparison summary"
echo "=========================================="

SUMMARY="$OUT_DIR/comparison-summary.md"

cat > "$SUMMARY" << EOF
# V1 vs V2 Comparison Results

Generated: $(date)
Output directory: $OUT_DIR

## Output Files

| # | Query | Type | V1 Lines | V2 Lines | V1 Time | V2 Time |
|---|-------|------|----------|----------|---------|---------|
EOF

for i in "${!QUERIES[@]}"; do
  query="${QUERIES[$i]}"
  type="${TYPES[$i]}"
  slug=$(slugify "$query")
  num=$((i + 1))

  v1file="$V1_DIR/${num}-${slug}.txt"
  v2file="$V2_DIR/${num}-${slug}.txt"

  v1lines=$(wc -l < "$v1file" 2>/dev/null || echo "ERR")
  v2lines=$(wc -l < "$v2file" 2>/dev/null || echo "ERR")

  echo "| $num | \`$query\` | $type | $v1lines | $v2lines | — | — |" >> "$SUMMARY"
done

cat >> "$SUMMARY" << 'EOF'

## Quick Check: Key Features

For each query, check these v2 improvements:

- [ ] Query parsing display (`🔍 **{TOPIC}** · {QUERY_TYPE}`)
- [ ] Sparse citations (not every sentence)
- [ ] Bold topic headers in summary
- [ ] Emoji stats tree (`├─ 🟠 Reddit:`)
- [ ] Quality checklist applied to prompts
- [ ] Self-check (research grounding, not generic)

## Scoring Guide

Use the full scoring rubric from:
`docs/plans/2026-02-06-test-v1-vs-v2-comparison-plan.md`

## Next Step

Have Claude read all 34 output files and generate scored comparison:
```
Read all files in docs/test-results/v1-vs-v2-*/v1/ and v2/
Score each on the 7 dimensions from the test plan
Write the final analysis to docs/test-results/v1-vs-v2-*/analysis.md
```
EOF

echo ""
echo "✅ All done!"
echo ""
echo "📁 Results:  $OUT_DIR"
echo "📊 Summary:  $SUMMARY"
echo "📄 V1 files: $V1_DIR/"
echo "📄 V2 files: $V2_DIR/"
echo ""
echo "To review:"
echo "  open $OUT_DIR"
