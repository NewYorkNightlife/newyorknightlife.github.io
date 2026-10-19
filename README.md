# NYNightlife.com

Know before you go: dress code, age, cover and how to get in for NYC bars and clubs, with sources
and the date each fact was checked. Static HTML on GitHub Pages. Live site: https://nynightlife.com

## How it's built (Oct 2026 rebuild)

- `_build/` holds the generator and the data. GitHub Pages skips underscore folders, so none of it is served.
  - `_build/data/venues/*.json`: one file per venue. Every fact has a status (confirmed / likely /
    unconfirmed / unknown) and its sources. The `chat` block holds Nyla's tags and nicknames.
  - `_build/data/playbooks/*.json`: group-night pages, priced per person.
  - `build.py` and `pages.py` write the pages. `nyla.py` writes `data/venues.json` for the chatbot.
  - `concierge.js` is the source for `js/concierge.js` (Nyla, the chat helper).
- Rebuild: `python _build/build.py`, then `node _build/test_nyla.js .` (Nyla's answer tests).
- Pages that were retired in the rebuild are listed in `_build/REMOVED-2026-10.txt`. They can be restored
  from git history.

Never commit secrets: everything in this repo is public.
