#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
LATEST=$(ls "$ROOT"/blog/weekly/weekend-brief-*.html 2>/dev/null | sort | tail -n 1 || true)

if [[ -z "$LATEST" ]]; then
  echo "No weekly briefs found."
  exit 1
fi

echo "Latest weekly brief: $LATEST"

# quick sanity checks
if ! grep -q "2:00 PM" "$LATEST"; then
  echo "WARN: 2:00 PM timestamp text not found in latest brief"
fi

if ! grep -q "Sources" "$LATEST"; then
  echo "WARN: Sources section not found in latest brief"
fi

for src in "eventbrite.com" "timeout.com" "nycgo.com" "ra.co"; do
  if ! grep -q "$src" "$LATEST"; then
    echo "WARN: expected source missing: $src"
  fi
done

echo "Weekly brief sanity check complete."