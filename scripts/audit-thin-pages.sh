#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
MIN_CHARS="${MIN_CHARS:-1200}"

echo "Auditing HTML pages under: $ROOT"
echo "Threshold: $MIN_CHARS characters (visible text approximation)"
echo

printf "%-60s %10s\n" "PAGE" "CHARS"
printf "%-60s %10s\n" "----" "-----"

find "$ROOT" -type f -name '*.html' \
  ! -path '*/.git/*' \
  | sort \
  | while read -r f; do
      text_len=$(sed -E 's/<script[^>]*>[\s\S]*?<\/script>//g; s/<style[^>]*>[\s\S]*?<\/style>//g; s/<[^>]+>/ /g' "$f" | tr -s ' ' | wc -c | tr -d ' ')
      if [ "$text_len" -lt "$MIN_CHARS" ]; then
        printf "%-60s %10s\n" "$f" "$text_len"
      fi
    done
