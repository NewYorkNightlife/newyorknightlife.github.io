#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
LATEST=$(ls "$ROOT"/blog/weekly/weekend-brief-*.html 2>/dev/null | sort | tail -n 1 || true)

if [[ -z "$LATEST" ]]; then
  echo "No weekly briefs found."
  exit 1
fi

echo "Latest weekly brief: $LATEST"

warn=0
need_strings=(
  "NYC Weather Snapshot"
  "Weekend Overview"
  "Live Event Signals"
  "Top Neighborhoods"
  "Night Route Strategies"
  "Budget + Risk Strategy"
  "Plan Your NYC Night"
  "Execution Checklist"
  "Sources"
  "Editorial Note"
  "Final Takeaway"
  "2:00 PM"
  "methodology"
  "affiliate-disclosure"
)

for s in "${need_strings[@]}"; do
  if ! grep -qi "$s" "$LATEST"; then
    echo "WARN: required section/text missing: $s"
    warn=1
  fi
done

# Required internal links
for u in \
  "https://nynightlife.com/tonight" \
  "https://nynightlife.com/weekend" \
  "https://nynightlife.com/night-planner" \
  "https://nynightlife.com/venue-compare" \
  "https://nynightlife.com/safe-late-night-transport" \
  "https://nynightlife.com/blog/archive"; do
  if ! grep -q "$u" "$LATEST"; then
    echo "WARN: required internal link missing: $u"
    warn=1
  fi
done

# external links should include target blank + noopener somewhere in file
if ! grep -q 'target="_blank"' "$LATEST"; then
  echo "WARN: external links missing target=_blank"
  warn=1
fi
if ! grep -q 'rel="noopener' "$LATEST"; then
  echo "WARN: external links missing rel=noopener"
  warn=1
fi

# word count range
words=$(python3 - <<'PY' "$LATEST"
import re,sys
t=open(sys.argv[1],encoding='utf-8').read()
t=re.sub(r'<script[\s\S]*?</script>',' ',t)
t=re.sub(r'<style[\s\S]*?</style>',' ',t)
t=re.sub(r'<[^>]+>',' ',t)
t=re.sub(r'\s+',' ',t)
print(len(t.split()))
PY
)
echo "Word count: $words"
if [[ "$words" -lt 1800 || "$words" -gt 2700 ]]; then
  echo "WARN: word count out of expected range (1800-2700)"
  warn=1
fi

# source count
src_count=$(python3 - <<'PY' "$LATEST"
import re,sys
t=open(sys.argv[1],encoding='utf-8').read().lower()
i=t.find('<h2>sources</h2>')
section=t[i:] if i!=-1 else ''
print(len(re.findall(r'<a href="https?://', section)))
PY
)
echo "Sources links in sources section: $src_count"
if [[ "$src_count" -lt 4 ]]; then
  echo "WARN: fewer than 4 source links"
  warn=1
fi

echo "Weekly brief sanity check complete."
exit 0
