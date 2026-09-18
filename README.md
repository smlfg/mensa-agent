# mensa-notifier

Daily notifier that pulls the menu of a Mensa (student cafeteria) from
[imensa.de](https://www.imensa.de) and prints a compact summary suitable
for delivery to a chat platform.

## What it does

- Fetches the HTML of the day's menu page (no JavaScript required)
- Parses meal categories, dish descriptions, and prices
- Picks up to three representative meals:
  1. A main dish when present
  2. A vegetarian / vegan option
  3. One further dish to round out the selection
- Surfaces a vegetarian alternative even if the top three are non-veg
- Falls back to a short error message if the source cannot be reached

## Source

The imensa.de project mirrors menu plans from several German
Studierendenwerke. This repo is configured for
[Mensa am Bildungscampus, Heilbronn](https://www.imensa.de/heilbronn/mensa-am-bildungscampus/)
(Studierendenwerk Heidelberg), but the URL constants in `mensa_today.py`
can be swapped for any other imensa location.

## Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python mensa_today.py
```

## Run on a schedule

`hermes cron create --script mensa-notifier.sh --no-agent --deliver all --name "mensa-notifier-daily" "30 8 * * 1-5"`

The companion shell wrapper is expected at
`~/.hermes/profiles/<profile>/scripts/mensa-notifier.sh` and just
invokes the Python script with the project's virtualenv.

## License

MIT.
