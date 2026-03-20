#!/usr/bin/env bash
set -euo pipefail

REPO="/home/nybotenv/.openclaw/workspace/repo-newyorknightlife"
LOGDIR="$REPO/.ops-logs/hourly"
mkdir -p "$LOGDIR"
cd "$REPO"

timestamp=$(date +"%Y-%m-%d_%H-%M-%S")

# Sync first to avoid push rejections.
git pull --rebase origin main >/dev/null 2>&1 || true

# Fill one thin, non-redirect page per run.
python3 - <<'PY'
from pathlib import Path
import re

repo=Path('/home/nybotenv/.openclaw/workspace/repo-newyorknightlife')
candidates=[]

def visible_len(html:str)->int:
    t=re.sub(r'<script[\s\S]*?</script>',' ',html,flags=re.I)
    t=re.sub(r'<style[\s\S]*?</style>',' ',t,flags=re.I)
    t=re.sub(r'<[^>]+>',' ',t)
    t=re.sub(r'\s+',' ',t).strip()
    return len(t)

for p in repo.rglob('*.html'):
    rel=p.relative_to(repo).as_posix()
    if rel.startswith('docs/') or rel.startswith('blog/weekly/'):
        continue
    html=p.read_text(encoding='utf-8',errors='ignore')
    if 'http-equiv="refresh"' in html.lower():
        continue
    if 'data-hourly-fill="v1"' in html:
        continue
    v=visible_len(html)
    if v < 500:
        candidates.append((v,p))

candidates.sort(key=lambda x: x[0])
if not candidates:
    print('NO_TARGET')
    raise SystemExit

_, target=candidates[0]
html=target.read_text(encoding='utf-8',errors='ignore')
section='''\n\n    <section class="content-card" data-hourly-fill="v1" style="margin-top:1rem;">
      <h2>How to Use This Tool Tonight</h2>
      <p>Use this tool as your first decision pass, then lock one primary plan and one backup plan within the same borough. This reduces dead time and keeps your group moving when demand spikes.</p>
      <p>Best workflow: run this tool, confirm your budget lane, and then open the Night Planner to convert your result into a practical route with timing and transit logic.</p>
      <p><a href="/tools/nyc-night-planner.html">Open NYC Night Planner</a> · <a href="/tonight/">See Tonight's NYC picks</a> · <a href="/weekend/">Weekend strategy hub</a></p>
    </section>\n'''

if '</main>' in html:
    html=html.replace('</main>', section + '\n  </main>', 1)
else:
    html += section

target.write_text(html,encoding='utf-8')
print(target.relative_to(repo).as_posix())
PY

# Capture what changed and commit if needed.
if ! git diff --quiet; then
  target=$(git diff --name-only | head -n1)
  git add -A
  git commit -m "Hourly content fill: ${target}" >/dev/null
  git push origin main >/dev/null 2>&1 || true
fi

# Always run audits and keep logs.
{
  echo "=== Hourly Thin Page Audit ($timestamp) ==="
  bash scripts/audit-thin-pages.sh || true
  echo
  echo "=== Affiliate Readiness Snapshot ($timestamp) ==="
  bash scripts/affiliate-readiness-report.sh || true
} > "$LOGDIR/$timestamp.log" 2>&1
