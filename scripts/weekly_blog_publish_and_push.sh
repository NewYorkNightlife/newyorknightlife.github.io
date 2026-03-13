#!/usr/bin/env bash
set -euo pipefail

export TZ=America/New_York
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/.ops-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/weekly-blog-publish.log"
LOCK_FILE="$ROOT/.weekly-blog.lock"

{
  echo "==== $(date '+%Y-%m-%d %H:%M:%S %Z') weekly blog publish run ===="

  flock -n 9 || { echo "Lock busy; exiting."; exit 0; }

  cd "$ROOT"

  # hard guard: rules file must exist
  [[ -f "$ROOT/docs/BLOG_HARD_RULES.md" ]] || { echo "ERROR: docs/BLOG_HARD_RULES.md missing"; exit 1; }

  python3 scripts/weekly_blog_autopublish.py

  # hard gate: do NOT publish if QA fails
  if ! ./scripts/weekly-blog-check.sh .; then
    echo "ERROR: weekly-blog-check failed; aborting publish"
    exit 1
  fi

  if ! git diff --quiet; then
    git add blog/weekly blog/archive-weekly-briefs.html blog/index.html sitemap.xml
    git commit -m "Auto-publish weekly brief $(date +%F)"
    git push origin main
    echo "Push complete."
  else
    echo "No content changes; nothing to commit."
  fi
} 9>"$LOCK_FILE" >> "$LOG_FILE" 2>&1
