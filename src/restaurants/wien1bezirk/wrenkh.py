import datetime
import json
import re
import html
import time
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from src.models import Restaurant, MenuItem, DayMenu, MenuMeta, RestaurantMenu

URL = "https://wrenkh-wien.at/site/de/restaurant/mittagsmenue"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-AT,de;q=0.9,en;q=0.8",
    "Connection": "close",
}

WEEKDAYS = ["MO", "DI", "MI", "DO", "FR"]

WEEKDAY_LABELS = {
    "MO": "Monday",
    "DI": "Tuesday",
    "MI": "Wednesday",
    "DO": "Thursday",
    "FR": "Friday",
}

PYTHON_WEEKDAY_TO_WRENKH = {
    0: "MO",
    1: "DI",
    2: "MI",
    3: "DO",
    4: "FR",
}

KNOWN_TAGS = {
    "VEGAN",
    "VEGETARISCH",
}

STOP_MARKERS = {
    "Restaurant Bauernmarkt",
    "Tischreservierung",
    "Spezial",
    "Imbiss Rauhensteingasse",
    "Kochsalon",
    "Gutscheine",
    "Kontakt & Impressum",
    "AGB & Datenschutz",
}


def fetch_page_text() -> str:
    last_error = None

    for attempt in range(3):
        try:
            response = requests.get(
                URL,
                headers=HEADERS,
                timeout=(15, 45),
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text("\n", strip=True)

        except requests.RequestException as error:
            last_error = error
            print(f"[WARNING] Wrenkh fetch attempt {attempt + 1}/3 failed: {error}")
            time.sleep(5 * (attempt + 1))

    raise last_error

def clean_lines(text: str) -> list[str]:
    lines = []

    for line in text.splitlines():
        cleaned =  cleaned = clean_text(line)

        if cleaned:
            lines.append(cleaned)

    return lines

def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    return html.unescape(value).replace("\xa0", " ").strip()

def find_week_range(lines: list[str]) -> str | None:
    pattern = re.compile(r"^\d{2}\.\d{2}\.\s*-\s*\d{2}\.\d{2}\.$")

    for line in lines:
        if pattern.match(line):
            return line

    return None


def find_price_text(lines: list[str]) -> str | None:
    for line in lines:
        if "Gänge" in line and "€" not in line:
            return line

        if "Gänge" in line:
            return line

    return None


def extract_day_sections(lines: list[str]) -> dict[str, list[str]]:
    sections = {}

    for weekday in WEEKDAYS:
        start_index = None
        end_index = None

        for index, line in enumerate(lines):
            if line == weekday:
                start_index = index
                break

        if start_index is None:
            sections[weekday] = []
            continue

        for index in range(start_index + 1, len(lines)):
            line = lines[index]

            if line in WEEKDAYS:
                end_index = index
                break

            if line in STOP_MARKERS:
                end_index = index
                break

        if end_index is None:
            end_index = len(lines)

        sections[weekday] = lines[start_index + 1:end_index]

    return sections



def parse_menu_items(day_lines: list[str]) -> list[MenuItem]:
    items = []
    current_item_name = None
    current_description_parts = []
    current_tags = []

    for line in day_lines:
        if line in KNOWN_TAGS:
            if current_item_name:
                items.append(
                    MenuItem(
                        name=current_item_name,
                        description=" ".join(current_description_parts) if current_description_parts else None,
                        tags=[line],
                    )
                )

                current_item_name = None
                current_description_parts = []
                current_tags = []

            continue

        if current_item_name is None:
            current_item_name = line
        else:
            current_description_parts.append(line)

    # In case the last item has no tag
    if current_item_name:
        items.append(
            MenuItem(
                name=current_item_name,
                description=" ".join(current_description_parts) if current_description_parts else None,
                tags=current_tags,
            )
        )

    return items


def get_current_wrenkh_day() -> str | None:
    today = datetime.date.today()
    weekday_number = today.weekday()

    return PYTHON_WEEKDAY_TO_WRENKH.get(weekday_number)


def parse_wrenkh_menu() -> RestaurantMenu:
    warnings = []

    page_text = fetch_page_text()
    lines = clean_lines(page_text)

    week_range_text = find_week_range(lines)
    price_text = find_price_text(lines)

    if not week_range_text:
        warnings.append("Could not detect week range.")

    if not price_text:
        warnings.append("Could not detect price text.")

    raw_day_sections = extract_day_sections(lines)

    days = {}

    for weekday, day_lines in raw_day_sections.items():
        items = parse_menu_items(day_lines)

        days[weekday] = DayMenu(
            weekday=weekday,
            label=WEEKDAY_LABELS[weekday],
            items=items,
        )

        if not items:
            warnings.append(f"No menu items found for {weekday}.")

    current_day = get_current_wrenkh_day()

    fetched_at = datetime.datetime.now(
        ZoneInfo("Europe/Vienna")
    ).isoformat(timespec="seconds")

    restaurant = Restaurant(
        id="wrenkh",
        name="Wrenkh",
        address="Bauernmarkt 10, 1010 Wien",
        source_url=URL,
    )

    meta = MenuMeta(
        fetched_at=fetched_at,
        parser="wrenkh",
        status="success",
        warnings=warnings,
    )

    return RestaurantMenu(
        restaurant=restaurant,
        menu_type="weekly_lunch_menu",
        week_range_text=week_range_text,
        price_text=price_text,
        serving_time="MO–FR, bis 15:00",
        current_day=current_day,
        days=days,
        meta=meta,
    )


def main():
    menu = parse_wrenkh_menu()
    menu_dict = menu.to_dict()

    print(json.dumps(menu_dict, ensure_ascii=False, indent=2))

    with open("wrenkh_menu.json", "w", encoding="utf-8") as file:
        json.dump(menu_dict, file, ensure_ascii=False, indent=2)

    print("\nSaved to wrenkh_menu.json")


if __name__ == "__main__":
    main()