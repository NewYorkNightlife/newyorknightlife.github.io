# n8n Setup — NYC Tonight Production Workflow

## 1) Import
- In n8n: **Workflows → Import from file**
- Select: `workflows/n8n/nyc-tonight-production.json`

## 2) Required credentials
Configure these nodes before enabling:

1. **OpenWeather (HTTP Request)**
   - Add API key in node query `appid`
2. **News provider (HTTP Request)**
   - Example: NewsAPI `apiKey`
3. **Event source A / B / C (HTTP Request)**
   - Use your approved sources/APIs
4. **AI QA (HTTP Request to OpenAI/compatible endpoint)**
   - Set bearer token
5. **GitHub publish nodes**
   - Token with `repo` scope
   - Owner: `NewYorkNightlife`
   - Repo: `newyorknightlife.github.io`
   - Path: `data/tonight-feed.json`

## 3) Verification policy
Featured events must satisfy all:
- 3 independent sources confirm same event
- date + time window align
- venue/location align
- not canceled/sold out (or clearly flagged)

If event fails verification: do not publish as featured.

## 4) Schedule (recommended)
- 11:00 AM ET
- 4:00 PM ET
- 8:10 PM ET

## 5) Output contract
Workflow writes JSON to:
- `/data/tonight-feed.json`

Schema:
- `workflows/n8n/tonight-feed.schema.json`

## 6) Safety
- If pipeline fails, stop before publish and keep previous file.
- Add alert step (Slack/Telegram/email) for failures.
