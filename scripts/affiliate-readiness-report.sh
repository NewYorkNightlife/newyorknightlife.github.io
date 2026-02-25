#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
TRACKER="$ROOT/docs/affiliate-program-tracker.csv"
QUEUE="$ROOT/docs/affiliate-deployment-queue.csv"

echo "=== Affiliate Program Status ==="
awk -F',' 'NR==1{next} {printf "- %s | status=%s | next=%s\n", $1,$3,$8}' "$TRACKER"

echo
echo "=== Deployment Queue Status ==="
awk -F',' 'NR==1{next} {printf "- P%s %s | %s | %s\n", $1,$2,$3,$4}' "$QUEUE"

echo
echo "=== Quick Counts ==="
submitted=$(awk -F',' 'NR>1 && $3 ~ /submitted|approved/ {c++} END{print c+0}' "$TRACKER")
approved=$(awk -F',' 'NR>1 && $3 ~ /approved/ {c++} END{print c+0}' "$TRACKER")
ready=$(awk -F',' 'NR>1 && $4 ~ /deployed/ {c++} END{print c+0}' "$QUEUE")

echo "Programs submitted/approved: $submitted"
echo "Programs approved: $approved"
echo "Queue deployed: $ready"
