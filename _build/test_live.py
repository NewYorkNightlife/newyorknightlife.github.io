"""Tests for the live-data job's handling of untrusted input. Run: python _build/test_live.py"""
import datetime as dt
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import live  # noqa: E402
import extras  # noqa: E402

fails = 0


def check(name, cond):
    global fails
    if not cond:
        fails += 1
        print("FAIL", name)


H = ["evgrieve.com"]
check("javascript link dropped", live.safe_link("javascript:alert(1)", H) is None)
check("data link dropped", live.safe_link("data:text/html,<b>x</b>", H) is None)
check("other host dropped", live.safe_link("https://evil.example/evgrieve.com/x", H) is None)
check("lookalike host dropped", live.safe_link("https://evgrieve.com.evil.example/x", H) is None)
check("http upgraded", live.safe_link("http://evgrieve.com/a?b=1#c", H) == "https://evgrieve.com/a?b=1")
check("subdomain ok", live.safe_link("https://www.evgrieve.com/x", H) == "https://www.evgrieve.com/x")

t = live.clean_text('<img src=x onerror=alert(1)>Bar &amp; <b>Lounge</b> opens')
check("tags stripped", "<" not in t and "onerror" not in t and t == "Bar & Lounge opens")
check("length capped", len(live.clean_text("x" * 500, 200)) <= 201)

for bad in (b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><r>&a;</r>', b"<!doctype html><html></html>"):
    try:
        live.parse_xml(bad)
        check("doctype refused", False)
    except ValueError:
        pass

feed = {"name": "T", "hosts": H, "nyc_only": True}
root = live.parse_xml(b'<rss><channel><item><title>&lt;script&gt;x&lt;/script&gt;New bar opens</title>'
                      b'<link>javascript:alert(1)</link><pubDate>Thu, 22 Oct 2026 10:00:00 +0000</pubDate></item>'
                      b'<item><title>A new cocktail bar on Avenue B</title><link>http://evgrieve.com/2026/10/x.html</link>'
                      b'<pubDate>Thu, 22 Oct 2026 10:00:00 +0000</pubDate></item></channel></rss>')
items = live.feed_items(feed, root)
check("script title neutralised", "<" not in items[0]["title"])
check("bad link item has no url", items[0]["url"] is None)
check("good item kept", items[1]["url"] == "https://evgrieve.com/2026/10/x.html")

s, v = live.score("On tonight's CB3-SLA docket: A new bar for the La Linea space", [], True, ["House of Yes"])
check("bar docket scores high", s >= 4)
s, v = live.score("New pizzeria opens in Hudson, NY", [], False, [])
check("away food item scores low", s < 4)
s, v = live.score("Shooting outside a bar in Queens", [], False, [])
check("crime news dampened", s < 6)
s, v = live.score("Halloween party at House of Yes", [], True, ["House of Yes"])
check("venue mention tagged", v == ["House of Yes"] and s >= 4)

check("entity name shown", bool(live.ENTITY.search("ACME HOSPITALITY LLC")))
check("person name hidden", not live.ENTITY.search("SOPHIA YOUN BOK KO"))

check("span text", extras.span_text("17:00-27:30") == "5pm–3:30am")
check("span midnight", extras.span_text("16:00-24:00") == "4pm–midnight")
check("span late", extras.span_text("12:00-late") == "noon–late" or extras.span_text("12:00-late") == "12pm–late")
check("close order", extras.close_mins("18:00-28:00") > extras.close_mins("18:00-26:00"))

# hardening from the final security review
check("userinfo trick dropped", live.safe_link(r"https://evil.com\@evgrieve.com/x", H) is None)
check("userinfo dropped", live.safe_link("https://evgrieve.com@evil.com/x", H) is None)
check("port dropped", live.safe_link("https://evgrieve.com:8443/x", H) is None)
check("double-encoded markup neutralised", "<" not in live.clean_text("&amp;lt;img src=x onerror=alert(1)&amp;gt;"))
for u in ("file:///etc/passwd", "http://api.weather.gov/x", "https://evil.example/x"):
    try:
        live.fetch(u); check("fetch refused " + u, False)
    except ValueError:
        pass
try:
    live.parse_xml('<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE r [<!ENTITY a "x">]><r>&a;</r>'.encode("utf-16"))
    check("utf-16 doctype refused", False)
except ValueError:
    pass
check("co/club names hidden", not live.ENTITY.search("JOHN CO") and not live.ENTITY.search("MARY CLUB"))

print(f"{'OK' if not fails else str(fails) + ' FAILED'}: live-data input tests")
sys.exit(1 if fails else 0)
