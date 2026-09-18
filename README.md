# Mensa Notifier

> A small Python CLI that fetches the daily menu of a German university
> *Mensa* from [imensa.de](https://www.imensa.de) and prints a compact,
> chat-ready summary.

Targeted at the **Mensa am Bildungscampus, Heilbronn** (Studierendenwerk
Heidelberg). About 190 lines of Python — `requests` + `BeautifulSoup`,
no database, no JavaScript, no secrets.

```
$ python mensa_today.py
Mensa am Bildungscampus - Speiseplan für Freitag heute

1. Vegetarisch: Tortellini mit Gemüsefüllung mit cremiger Gorgonzolasoße / 2,90 €
```

---

## What it does

- Fetches the day's menu page (plain HTML, no JS rendering required)
- Parses meal categories, dish descriptions, and prices
- Picks up to three representative meals in a deterministic order:
  1. A main dish (*Menu 1 / Menu 2 / Tagesgericht / Hauptgericht*) when present
  2. A vegetarian / vegan option
  3. One further dish to round out the selection
- Surfaces a vegetarian alternative as a fallback line even when the top
  three picks are all non-veg
- Prints a short, human-readable error message if `imensa.de` cannot be reached

---

## How it works

```
+-------------+    HTTP GET     +---------------------+
| mensa_today | --------------► | imensa.de/heilbronn |
|     .py     | ◄--------------- | /index.html (HTML)  |
+-----+-------+    HTML text     +----------+----------+
      │                                       │
      │ BeautifulSoup selectors               │
      ▼                                       ▼
+----------------+   _clean() / _strip_price_marker()
| parse_meals()  | -----------------------------+
+-----+----------+                               │
      │ list[Meal]                              ▼
      ▼                                +-----------------+
+----------+    pick_relevant()       | format_message()|
| pick 3   | ----------------------►  |  print to stdout|
+----------+                           +-----------------+
```

Five functions do all the work: `fetch_today_html`, `parse_date_from_html`,
`parse_meals`, `pick_relevant`, `format_message`. Everything is plain
synchronous I/O — `requests` with a 20-second timeout, then one HTML parse.

---

## Run it

```bash
git clone https://github.com/smlfg/mensa-agent.git
cd mensa-agent

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python mensa_today.py
```

Requires Python 3.10+ (uses `X | None` type hints).

---

## Configure for a different Mensa

The script is hardcoded for Heilbronn but is trivially retargetable by
editing two constants at the top of `mensa_today.py`:

```python
BASE_URL = "https://www.imensa.de/<city>/<mensa-slug>/"
TODAY_URL = BASE_URL + "index.html"
```

Any imensa location with the same HTML structure (`div.aw-meal-category`,
`p.aw-meal-description`, `div.aw-meal-price`) will work without further
changes. On weekends the script switches to a weekday-slug URL
(`montag.html`, `dienstag.html`, …) to read the coming week's plan.

---

## Run it on a schedule

Designed to be invoked from a daily cron / scheduled agent. The canonical
deployment uses [Hermes Agent](https://hermes-agent.nousresearch.com/docs):

```bash
hermes cron create --script mensa-notifier.sh --no-agent \
    --deliver all --name "mensa-notifier-daily" "30 8 * * 1-5"
```

The companion shell wrapper is expected at
`~/.hermes/profiles/<profile>/scripts/mensa-notifier.sh` and just calls
the Python script with the project's virtualenv activated.

---

## Project layout

```
.
├── mensa_today.py     # the whole program (~190 lines)
├── requirements.txt   # requests, beautifulsoup4
├── README.md
├── LICENSE            # MIT
└── .gitignore         # ignores .venv, planning notes, etc.
```

---

## Limitations, honestly

- **Brittle to imensa's HTML.** Selectors like `div.aw-meal-category` are
  tied to the live site. If Studierendenwerk Heidelberg changes their
  template, the parser will silently return an empty list. There is no
  test suite.
- **One URL at a time.** No multi-location mode, no historical menus,
  no price normalisation across student / staff / guest tiers.
- **No notifications built in.** It only prints to stdout. Delivery to
  Telegram / WhatsApp / e-mail is handled by the calling scheduler.
- **No retry / backoff.** A transient 5xx produces the fallback error
  message and exits 1; the next cron tick is expected to recover.

This is a single-purpose utility, not a framework.

---

## License

[MIT](LICENSE) — © 2025 Samuel.
