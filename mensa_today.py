#!/usr/bin/env python3
"""Kompaktes Tagespaket fuer eine imensa.de-Mensa.

Quelle: imensa.de (oeffentlicher Speiseplan-Spiegel mehrerer Studierendenwerke).
Kein Dashboard, keine DB, keine Secrets. Nur HTML -> Parser -> Textausgabe.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from dataclasses import dataclass
from typing import Iterable

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.imensa.de/heilbronn/mensa-am-bildungscampus/"
TODAY_URL = BASE_URL + "index.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (mensa-notifier; private daily notifier)",
}

# Wochentag -> URL-Pfad (imensa nutzt deutsch kleingeschrieben)
WEEKDAY_SLUGS = {
    0: "montag",
    1: "dienstag",
    2: "mittwoch",
    3: "donnerstag",
    4: "freitag",
    5: "samstag",
    6: "sonntag",
}


@dataclass
class Meal:
    category: str
    description: str
    price: str = ""

    def compact(self) -> str:
        parts = [self.description]
        if self.price:
            parts.append(self.price)
        return " / ".join(part for part in parts if part)

    def is_vegan_or_veg(self) -> bool:
        """Heuristik: Kategorie-Name + Beschreibungs-Text pruefen."""
        text = (self.category + " " + self.description).lower()
        return any(
            marker in text
            for marker in ("vegan", "vegetarisch", "veggie", "pflanzlich")
        )


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+,", ",", text)
    return text


def _strip_price_marker(text: str) -> str:
    """imensa markiert Preise als '2,90 EUR' mit Non-Breaking-Space."""
    return text.replace("\xa0", " ").strip()


def fetch_today_html(today: dt.date | None = None) -> str:
    """Hole den Tagesplan. Heute -> index.html, sonst Wochentag-Slug."""
    if today is None:
        today = dt.date.today()
    if today.weekday() >= 5:
        slug = WEEKDAY_SLUGS[today.weekday()]
        url = BASE_URL + slug + ".html"
    else:
        url = TODAY_URL

    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def parse_date_from_html(html: str) -> str:
    """Datum aus dem HTML extrahieren -- imensa schreibt es in den H2-Titel."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one(".aw-menu-title")
    if title:
        return _clean(title.get_text(" ", strip=True))
    return f"Heute, {dt.date.today().strftime('%d.%m.%Y')}"


def parse_meals(html: str) -> list[Meal]:
    """Extrahiere alle Mahlzeiten gruppiert nach Kategorie."""
    soup = BeautifulSoup(html, "html.parser")
    meals: list[Meal] = []

    for category_div in soup.select("div.aw-meal-category"):
        category_name_el = category_div.select_one("h3.aw-meal-category-name")
        category_name = _clean(category_name_el.get_text(" ", strip=True)) if category_name_el else ""

        for meal_div in category_div.select("div.aw-meal"):
            desc_el = meal_div.select_one("p.aw-meal-description")
            price_el = meal_div.select_one("div.aw-meal-price")
            if not desc_el:
                continue
            description = _clean(desc_el.get_text(" ", strip=True))
            price = _strip_price_marker(price_el.get_text(" ", strip=True)) if price_el else ""
            if description:
                meals.append(
                    Meal(category=category_name, description=description, price=price)
                )

    return meals


def pick_relevant(meals: Iterable[Meal]) -> list[Meal]:
    """Waehle bis zu 3 repraesentative Mahlzeiten:
    1. erstes Hauptgericht (falls vorhanden)
    2. vegetarische/vegane Option
    3. ein weiteres vielfaeltiges Gericht
    """
    meals = list(meals)
    if not meals:
        return []

    picked: list[Meal] = []

    def add_first(predicate) -> None:
        for meal in meals:
            if meal in picked:
                continue
            if predicate(meal):
                picked.append(meal)
                return

    add_first(lambda m: any(
        kw in m.category.lower() for kw in ("menu 1", "menu 2", "tagesgericht", "hauptgericht")
    ))
    add_first(lambda m: m.is_vegan_or_veg())

    for meal in meals:
        if len(picked) >= 3:
            break
        if meal not in picked:
            picked.append(meal)

    return picked[:3]


def format_message(date_label: str, all_meals: list[Meal]) -> str:
    """Format: Header + 3 Menues + Veggie-Hinweis."""
    lines = [f"Mensa am Bildungscampus - {date_label}", ""]

    if not all_meals:
        lines.append("Heute keine Gerichte in der Datenbank (Wochenende oder Feiertag?).")
        lines.append(f"Quelle: {TODAY_URL}")
        return "\n".join(lines)

    picked = pick_relevant(all_meals)
    for idx, meal in enumerate(picked, start=1):
        category = meal.category or "Gericht"
        lines.append(f"{idx}. {category}: {meal.compact()}")

    has_veg = any(m.is_vegan_or_veg() for m in picked)
    if not has_veg:
        veg_alternatives = [m for m in all_meals if m.is_vegan_or_veg()]
        if veg_alternatives:
            lines.append("")
            lines.append(f"Veggie/Vegan-Option: {veg_alternatives[0].compact()}")

    lines.append("")
    lines.append(f"Quelle: {TODAY_URL}")
    return "\n".join(lines)


def main() -> int:
    try:
        html = fetch_today_html()
        date_label = parse_date_from_html(html)
        all_meals = parse_meals(html)
        print(format_message(date_label, all_meals))
        return 0
    except Exception as exc:
        print("Mensa am Bildungscampus - Heute", file=sys.stdout)
        print("", file=sys.stdout)
        print(f"Fehler: Speiseplan konnte nicht geladen werden ({exc}).", file=sys.stdout)
        print(f"Quelle: {TODAY_URL}", file=sys.stdout)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
