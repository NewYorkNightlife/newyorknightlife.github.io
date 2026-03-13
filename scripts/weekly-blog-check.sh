#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
LATEST=$(ls "$ROOT"/blog/weekly/weekend-brief-*.html 2>/dev/null | sort | tail -n 1 || true)

if [[ -z "$LATEST" ]]; then
  echo "No weekly briefs found."
  exit 1
fi

echo "Latest weekly brief: $LATEST"

# previous weekly brief for comparison gates
prev=$(ls "$ROOT"/blog/weekly/weekend-brief-*.html 2>/dev/null | sort | tail -n 2 | head -n 1 || true)

warn=0
need_strings=(
  "NYC Weather Snapshot"
  "Weekend Overview"
  "What Changed This Week"
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

# Weather numeric checks (must include both Fahrenheit and Celsius)
f_count=$(grep -o '°F' "$LATEST" | wc -l | tr -d ' ')
c_count=$(grep -o '°C' "$LATEST" | wc -l | tr -d ' ')
echo "Weather unit markers: °F=$f_count °C=$c_count"
if [[ "$f_count" -lt 8 || "$c_count" -lt 8 ]]; then
  echo "WARN: weather block must include numeric °F and °C values (current + 7-day range)"
  warn=1
fi

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
if [[ "$words" -lt 2500 || "$words" -gt 3000 ]]; then
  echo "WARN: word count out of required range (2500-3000)"
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

# image + caption requirement
img_count=$(grep -oi '<img ' "$LATEST" | wc -l | tr -d ' ')
cap_count=$(grep -oi '<figcaption' "$LATEST" | wc -l | tr -d ' ')
echo "Image count: $img_count | Caption count: $cap_count"
if [[ "$img_count" -lt 2 || "$cap_count" -lt 2 ]]; then
  echo "WARN: require at least 2 embedded images and 2 captions"
  warn=1
fi

# image uniqueness vs previous week
if [[ -n "$prev" && -f "$prev" ]]; then
  img_cmp=$(python3 - <<'PY' "$LATEST" "$prev"
import re,sys
n=open(sys.argv[1],encoding='utf-8').read().lower()
p=open(sys.argv[2],encoding='utf-8').read().lower()
get=lambda t:set(re.findall(r'<img[^>]+src="([^"]+)"',t))
a=get(n); b=get(p)
print(f"current_imgs={len(a)} prev_imgs={len(b)} shared={len(a & b)}")
print('FAIL' if a and a==b else 'PASS')
PY
)
  echo "Image uniqueness check: ${img_cmp%%$'\n'*}"
  if grep -q 'FAIL' <<< "$img_cmp"; then
    echo "WARN: image src set identical to previous weekly brief"
    warn=1
  fi
fi

# external link validation
link_report=$(python3 - <<'PY' "$LATEST"
import re,sys,requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

html=open(sys.argv[1],encoding='utf-8').read()
urls=sorted(set(re.findall(r'href="(https?://[^"]+)"', html)))

s=requests.Session()
retries=Retry(total=2, backoff_factor=0.3, status_forcelist=[429,500,502,503,504], allowed_methods=["HEAD","GET"])
s.mount('http://', HTTPAdapter(max_retries=retries))
s.mount('https://', HTTPAdapter(max_retries=retries))

bad=[]
for u in urls:
    try:
        r=s.head(u, allow_redirects=True, timeout=12)
        code=r.status_code
        if code>=400 or code<200:
            r=s.get(u, allow_redirects=True, timeout=12)
            code=r.status_code
        if code<200 or code>=400:
            bad.append((u,code))
    except Exception:
        bad.append((u,'ERR'))

print(f"external_urls={len(urls)} bad={len(bad)}")
for u,c in bad[:10]:
    print(f"BAD {c} {u}")
if bad:
    print('FAIL')
else:
    print('PASS')
PY
)
echo "Link check: ${link_report%%$'\n'*}"
if grep -q 'FAIL' <<< "$link_report"; then
  echo "$link_report" | sed -n '2,12p'
  echo "WARN: one or more external links failed validation"
  warn=1
fi

# uniqueness check against previous weekly brief
if [[ -n "$prev" && -f "$prev" ]]; then
  uniq_report=$(python3 - <<'PY' "$LATEST" "$prev"
import re,sys
new=open(sys.argv[1],encoding='utf-8').read().lower()
old=open(sys.argv[2],encoding='utf-8').read().lower()

def clean(t):
    t=re.sub(r'<script[\s\S]*?</script>',' ',t)
    t=re.sub(r'<style[\s\S]*?</style>',' ',t)
    t=re.sub(r'<[^>]+>',' ',t)
    t=re.sub(r'\s+',' ',t)
    return t.strip()

def ngrams(words,n=4):
    return set(tuple(words[i:i+n]) for i in range(len(words)-n+1)) if len(words)>=n else set()

def sentences(t):
    s=[x.strip() for x in re.split(r'(?<=[.!?])\s+',t) if len(x.strip())>60]
    return s

n=clean(new); o=clean(old)
nw=n.split(); ow=o.split()
ng_n=ngrams(nw,4); ng_o=ngrams(ow,4)
inter=len(ng_n & ng_o); uni=max(1,len(ng_n | ng_o))
sim=inter/uni
sn=sentences(n); so=set(sentences(o))
overlap=sum(1 for x in sn if x in so)
ratio=(overlap/max(1,len(sn)))
print(f"ngram_jaccard={sim:.3f} sentence_overlap={ratio:.3f}")
if sim>0.35 and ratio>0.35:
    print("FAIL")
else:
    print("PASS")
PY
)
  echo "Uniqueness check vs previous: ${uniq_report%%$'\n'*}"
  if grep -q "FAIL" <<< "$uniq_report"; then
    echo "WARN: content too similar to previous week (target: >=80% unique)"
    warn=1
  fi
fi

echo "Weekly brief sanity check complete."
exit 0
