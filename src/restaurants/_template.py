"""
Template parser for a new restaurant.

How to use this file:
1. Copy this file.
2. Rename it, for example:
   src/restaurants/example_restaurant.py
3. Rename parse_template_menu() to something restaurant-specific:
   parse_example_restaurant_menu()
4. Fill in the fetch/parse logic.
5. Register the parser in:
   src/restaurants/registry.py

Every restaurant parser should return a RestaurantMenu object.
"""

import datetime
import html
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from ..models import Restaurant, MenuItem, DayMenu, MenuMeta, RestaurantMenu


# ---------------------------------------------------------------------------
# Basic restaurant configuration
# ---------------------------------------------------------------------------

RESTAURANT_ID = "template"
RESTAURANT_NAME = "Template Restaurant"
RESTAURANT_ADDRESS = "Street 1, 1010 Wien"
SOURCE_URL = "https://example.com/menu"

WEEKDAYS = ["MO", "DI", "MI", "DO", "FR"]

WEEKDAY_LABELS = {
    "MO": "Monday",
    "DI": "Tuesday",
    "MI": "Wednesday",
    "DO": "Thursday",
    "FR": "Friday",
}

PYTHON_WEEKDAY_TO_MENU_WEEKDAY = {
    0: "MO",
    1: "DI",
    2: "MI",
    3: "DO",
    4: "FR",
}


# Optional: use browser-like headers if the website blocks simple scripts.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-AT,de;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------

def clean_text(value: str | None) -> str | None:
    """
    Clean text from HTML/PDF/websites.

    Converts:
    - &amp; to &
    - non-breaking spaces to normal spaces
    - surrounding whitespace removed
    """
    if value is None:
        return None

    return html.unescape(str(value)).replace("\xa0", " ").strip()


def get_current_menu_day() -> str | None:
    """
    Returns today's weekday key in our internal format:
    MO, DI, MI, DO, FR

    Returns None on weekends.
    """
    today = datetime.date.today()
    return PYTHON_WEEKDAY_TO_MENU_WEEKDAY.get(today.weekday())


def empty_day_menus() -> dict[str, DayMenu]:
    """
    Creates empty DayMenu objects for MO-FR.
    """
    return {
        weekday: DayMenu(
            weekday=weekday,
            label=WEEKDAY_LABELS[weekday],
            items=[],
        )
        for weekday in WEEKDAYS
    }


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_page_html() -> str:
    """
    Fetch raw HTML from the restaurant website.

    Replace this if the restaurant uses:
    - PDF menus
    - images
    - JavaScript rendering
    - an API endpoint
    """
    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    return response.text


def extract_visible_text_from_html(html_content: str) -> list[str]:
    """
    Converts HTML into clean visible text lines.

    This is useful for simple websites where the menu is directly visible
    in the HTML.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    raw_text = soup.get_text("\n", strip=True)

    lines = []

    for line in raw_text.splitlines():
        cleaned = clean_text(line)

        if cleaned:
            lines.append(cleaned)

    return lines


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_menu_lines(lines: list[str]) -> dict[str, DayMenu]:
    """
    Convert extracted text lines into our common DayMenu structure.

    This is intentionally empty/barebones.
    Each restaurant website has a different structure, so implement the
    restaurant-specific parsing here.

    Example target structure:

    days["MO"].items.append(
        MenuItem(
            name="Tomato soup",
            description="with basil",
            price="€ 8,90",
            tags=["VEGETARIAN"],
        )
    )
    """
    days = empty_day_menus()

    # TODO:
    # 1. Find menu section in `lines`
    # 2. Detect weekday sections
    # 3. Extract dish name, description, price, tags
    # 4. Append MenuItem objects to the correct DayMenu

    return days


def find_week_range(lines: list[str]) -> str | None:
    """
    Optional:
    Detect a week range like:
    01.07. - 05.07.
    or
    von 01.07.2026 bis 05.07.2026
    """
    # TODO: implement if available
    return None


def find_price_text(lines: list[str]) -> str | None:
    """
    Optional:
    Detect general price information, for example:
    2 courses for € 16,00
    """
    # TODO: implement if available
    return None


def find_serving_time(lines: list[str]) -> str | None:
    """
    Optional:
    Detect serving time, for example:
    MO-FR until 15:00
    """
    # TODO: implement if available
    return None


# ---------------------------------------------------------------------------
# Main parser function
# ---------------------------------------------------------------------------

def parse_template_menu() -> RestaurantMenu:
    """
    Main entry point for this restaurant parser.

    IMPORTANT:
    Every parser should expose exactly one function like this, returning
    RestaurantMenu.

    Later, register this function in:
    src/restaurants/registry.py
    """
    warnings = []

    html_content = fetch_page_html()
    lines = extract_visible_text_from_html(html_content)

    days = parse_menu_lines(lines)

    week_range_text = find_week_range(lines)
    price_text = find_price_text(lines)
    serving_time = find_serving_time(lines)

    if not any(day.items for day in days.values()):
        warnings.append("No menu items found.")

    fetched_at = datetime.datetime.now(
        ZoneInfo("Europe/Vienna")
    ).isoformat(timespec="seconds")

    restaurant = Restaurant(
        id=RESTAURANT_ID,
        name=RESTAURANT_NAME,
        address=RESTAURANT_ADDRESS,
        source_url=SOURCE_URL,
    )

    meta = MenuMeta(
        fetched_at=fetched_at,
        parser=RESTAURANT_ID,
        status="success" if not warnings else "partial",
        warnings=warnings,
    )

    return RestaurantMenu(
        restaurant=restaurant,
        menu_type="weekly_lunch_menu",
        week_range_text=week_range_text,
        price_text=price_text,
        serving_time=serving_time,
        current_day=get_current_menu_day(),
        days=days,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Local debug run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    menu = parse_template_menu()

    print(json.dumps(menu.to_dict(), ensure_ascii=False, indent=2))
