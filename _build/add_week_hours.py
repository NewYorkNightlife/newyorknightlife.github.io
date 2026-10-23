"""One-off (2026-10-23): add a structured "week" block to each venue's hours fact.

Transcribed by hand from that venue's checked hours text (same sources, same status).
Times are 24h; a close past midnight is written as 24+ (e.g. "27:00" = 3am next morning).
kind: "fixed" = regular opening hours; "event" = only open for events (never shown as "open tonight").
A missing day = closed or not published (see the hours text).
"""
import json
import pathlib

D = pathlib.Path(__file__).resolve().parent / "data" / "venues"
ALL = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def each(days, span):
    return {d: span for d in days}


WEEK = {
    "230-fifth-rooftop": ("fixed", {**each(["mon", "tue", "wed", "thu"], "12:00-25:30"), "fri": "12:00-late",
                                     "sat": "11:00-28:00", "sun": "11:00-25:30"}),
    "attaboy": ("fixed", each(ALL, "17:00-27:00")),
    "beauty-and-essex": ("fixed", {**each(["tue", "wed", "sun"], "17:00-22:00"), "thu": "17:00-23:00",
                                    **each(["fri", "sat"], "17:00-24:00")}),
    "bossa-nova-civic-club": ("fixed", each(ALL, "22:00-27:30")),
    "death-and-co": ("fixed", {**each(["sun", "mon", "tue", "wed"], "18:00-25:00"), **each(["thu", "fri", "sat"], "18:00-26:00")}),
    "elsewhere": ("event", {}),
    "employees-only": ("fixed", each(ALL, "18:00-28:00")),
    "good-room": ("event", {}),
    "harriets-rooftop": ("fixed", {**each(["mon", "tue", "wed", "thu"], "12:00-23:00"), **each(["fri", "sat"], "11:00-24:00"),
                                    "sun": "11:00-23:00"}),
    "house-of-yes": ("event", {}),
    "knockdown-center": ("event", {}),
    "le-bain": ("fixed", {**each(["wed", "thu", "fri"], "16:00-28:00"), "sat": "14:00-28:00", "sun": "14:00-24:00"}),
    "magic-hour-rooftop": ("fixed", {**each(["mon", "tue", "wed"], "17:00-24:00"), "thu": "17:00-26:00", "fri": "17:00-28:00",
                                      "sat": "11:30-28:00", "sun": "11:30-24:00"}),
    "marquee-new-york": ("fixed", each(["wed", "fri", "sat"], "23:00-28:00")),
    "mr-purple": ("fixed", {**each(["mon", "tue", "wed"], "16:00-26:00"), "thu": "16:00-27:00", "fri": "16:00-28:00",
                             "sat": "14:00-28:00", "sun": "14:00-26:00"}),
    "musica-club": ("event", {}),
    "nebula": ("fixed", each(["tue", "fri", "sat"], "23:00-28:00")),
    "nowadays": ("fixed", {"thu": "17:00-24:00", "fri": "17:00-27:00", "sat": "14:00-27:00", "sun": "15:00-21:00"}),
    "ophelia-lounge": ("fixed", {**each(["sun", "mon", "tue", "wed"], "17:00-23:00"), "thu": "17:00-24:00",
                                  **each(["fri", "sat"], "17:00-26:00")}),
    "pacha-new-york": ("event", {}),
    "paragon": ("event", {}),
    "phd-rooftop-lounge": ("fixed", each(["wed", "thu", "fri", "sat"], "22:00-28:00")),
    "please-dont-tell": ("fixed", {**each(["sun", "mon", "tue", "wed", "thu"], "17:00-26:00"), **each(["fri", "sat"], "17:00-27:00")}),
    "public-records": ("fixed", {**each(["wed", "thu"], "18:00-22:00"), "fri": "18:00-28:00", "sat": "10:00-28:00", "sun": "10:00-21:00"}),
    "somewhere-nowhere": ("fixed", {"wed": "17:00-25:00", **each(["fri", "sat", "sun"], "12:00-28:00")}),
    "the-back-room": ("fixed", {**each(["sun", "mon"], "18:00-25:00"), **each(["tue", "wed", "thu"], "18:00-26:00"),
                                 **each(["fri", "sat"], "18:00-27:00")}),
    "the-box": ("fixed", each(["wed", "thu", "fri", "sat"], "23:00-28:00")),
    "the-dead-rabbit": ("fixed", {**each(["sun", "mon", "tue", "wed", "thu"], "11:00-26:00"), **each(["fri", "sat"], "11:00-27:00")}),
    "westlight": ("fixed", {**each(["mon", "tue", "wed", "thu"], "16:00-24:00"), "fri": "16:00-25:00", "sat": "12:00-26:00",
                             "sun": "12:00-24:00"}),
}

# Shown wherever the week is shown, when the table alone would mislead.
NOTE = {
    "nowadays": "Outdoor yard hours. Indoors runs Fri 10pm to about 6am; Nonstop runs Sat 10pm to Sun 10pm.",
    "the-dead-rabbit": "Taproom hours. The upstairs Parlor closes earlier (1am most nights).",
    "230-fifth-rooftop": "Friday has no published closing time; last entry 2am.",
}

for f in sorted(D.glob("*.json")):
    v = json.loads(f.read_text(encoding="utf-8"))
    if f.stem not in WEEK:  # e.g. closed venues
        v["hours"].pop("week", None)
        v["hours"].pop("kind", None)
    else:
        kind, week = WEEK[f.stem]
        v["hours"]["kind"] = kind
        v["hours"]["week"] = week
        if f.stem in NOTE:
            v["hours"]["note"] = NOTE[f.stem]
        else:
            v["hours"].pop("note", None)
    f.write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print("done")
