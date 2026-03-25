#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_DIR="$SCRIPT_DIR/output"
mkdir -p "$OUTPUT_DIR"

COMBINED_MD="$OUTPUT_DIR/_combined.md"
COMBINED_HTML="$OUTPUT_DIR/_combined.html"
FINAL_PDF="$OUTPUT_DIR/agentic-systems-course.pdf"

# Generation date
GEN_DATE=$(date '+%B %d, %Y')

# Part titles
declare -a PART_TITLES=(
  "Part 1: Foundations for the Backend Engineer"
  "Part 2: The Single Agent — Anatomy & Patterns"
  "Part 3: Multi-Agent Systems"
  "Part 4: Feedback, Learning & Continuous Improvement"
  "Part 5: Production Hardening"
  "Part 6: The Agent Platform — Building for Others"
  "Part 7: UX & Human-Agent Collaboration"
  "Part 8: Capstone & The Road Ahead"
)

# Part directories in order
declare -a PART_DIRS=(
  "part-1-foundations"
  "part-2-single-agent"
  "part-3-multi-agent"
  "part-4-feedback-learning"
  "part-5-production-hardening"
  "part-6-agent-platform"
  "part-7-ux-collaboration"
  "part-8-capstone"
)

echo "==> Building combined markdown..."

# Start fresh
> "$COMBINED_MD"

# --- Cover page ---
cat >> "$COMBINED_MD" << EOF
<div class="cover-page">
<h1 class="cover-title">Agentic System Design<br>& Design Patterns</h1>
<p class="cover-subtitle">From Zero to Platform Architect</p>
<p class="cover-date">Generated: $GEN_DATE</p>
</div>

<div class="page-break"></div>

EOF

# --- Preface (README.md) ---
cat >> "$COMBINED_MD" << 'EOF'
<div class="part-title-page">
<h1>Preface</h1>
</div>

<div class="page-break"></div>

EOF
cat "$SCRIPT_DIR/README.md" >> "$COMBINED_MD"
echo -e "\n\n<div class=\"page-break\"></div>\n" >> "$COMBINED_MD"

# --- Table of Contents placeholder (pandoc generates from headers) ---

# --- Parts and modules ---
for i in "${!PART_DIRS[@]}"; do
  part_dir="${PART_DIRS[$i]}"
  part_title="${PART_TITLES[$i]}"

  # Part title page
  cat >> "$COMBINED_MD" << EOF

<div class="part-title-page">
<h1 class="part-heading">$part_title</h1>
</div>

<div class="page-break"></div>

EOF

  # Add each module in order
  for module_file in $(ls "$SCRIPT_DIR/$part_dir"/*.md 2>/dev/null | sort); do
    cat "$module_file" >> "$COMBINED_MD"
    echo -e "\n\n<div class=\"page-break\"></div>\n" >> "$COMBINED_MD"
  done
done

# --- Appendices ---
cat >> "$COMBINED_MD" << 'EOF'

<div class="part-title-page">
<h1 class="part-heading">Appendices</h1>
</div>

<div class="page-break"></div>

# Appendix A: Glossary

EOF
cat "$SCRIPT_DIR/glossary.md" >> "$COMBINED_MD"
echo -e "\n\n<div class=\"page-break\"></div>\n" >> "$COMBINED_MD"

cat >> "$COMBINED_MD" << 'EOF'

# Appendix B: Patterns Index

EOF
cat "$SCRIPT_DIR/patterns-index.md" >> "$COMBINED_MD"

echo "==> Converting markdown to HTML via pandoc..."

pandoc "$COMBINED_MD" \
  -f markdown+smart \
  -t html5 \
  --standalone \
  --toc \
  --toc-depth=2 \
  --syntax-highlighting=kate \
  --metadata title="Agentic System Design & Design Patterns" \
  --css="$OUTPUT_DIR/_style.css" \
  -o "$COMBINED_HTML"

echo "==> Converting HTML to PDF via weasyprint..."

# weasyprint needs the CSS embedded or referenced; we inject it via pandoc --css
# but weasyprint reads the HTML file directly
/opt/homebrew/bin/python3.12 -m weasyprint "$COMBINED_HTML" "$FINAL_PDF"

echo "==> Done! PDF at: $FINAL_PDF"
echo "    Size: $(du -h "$FINAL_PDF" | cut -f1)"
