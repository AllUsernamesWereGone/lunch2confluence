import datetime
import html
import json
import re
import time
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from ...models import Restaurant, MenuItem, DayMenu, MenuMeta, RestaurantMenu


RESTAURANT_ID = "esterhazykeller"
RESTAURANT_NAME = "Esterházystüberl"
RESTAURANT_ADDRESS = "Haarhof 1, 1010 Wien"
SOURCE_URL = "https://www.esterhazykeller.at/stueberl"

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

GERMAN_WEEKDAY_TO_KEY = {
    "MONTAG": "MO",
    "DIENSTAG": "DI",
    "MITTWOCH": "MI",
    "DONNERSTAG": "DO",
    "FREITAG": "FR",
}

STOP_MARKERS = {
    "VALENTINSTAG",
    "SCHMANKERLKARTE",
    "SPEISEN",
    "GETRÄNKE",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-AT,de;q=0.9,en;q=0.8",
}


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    return (
        html.unescape(str(value))
        .replace("\xa0", " ")
        .replace("\u200b", "")
        .strip()
    )


def get_current_menu_day() -> str | None:
    today = datetime.date.today()
    return PYTHON_WEEKDAY_TO_MENU_WEEKDAY.get(today.weekday())


def fetch_page_text() -> str:
    last_error = None

    for attempt in range(3):
        try:
            response = requests.get(
                SOURCE_URL,
                headers=HEADERS,
                timeout=(15, 45),
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text("\n", strip=True)

        except requests.RequestException as error:
            last_error = error
            print(
                f"[WARNING] Esterházystüberl fetch attempt "
                f"{attempt + 1}/3 failed: {error}"
            )
            time.sleep(3 * (attempt + 1))

    raise last_error


def clean_lines(text: str) -> list[str]:
    lines = []

    for line in text.splitlines():
        cleaned = clean_text(line)

        if cleaned:
            lines.append(cleaned)

    return lines


def looks_like_week_range(line: str) -> bool:
    return bool(
        re.search(
            r"\d{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s*[–-]\s*\d{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s*\d{4}",
            line,
        )
    )


def find_real_lunch_start(lines: list[str]) -> int | None:
    """
    Wix page has MITTAGSMENÜS twice:
    - once in navigation
    - once as the actual section heading

    We want the one followed shortly by a week range.
    """
    for index, line in enumerate(lines):
        if line.upper() != "MITTAGSMENÜS":
            continue

        next_few_lines = lines[index + 1:index + 6]

        if any(looks_like_week_range(next_line) for next_line in next_few_lines):
            return index

    return None


def find_lunch_end(lines: list[str], start_index: int) -> int:
    for index in range(start_index + 1, len(lines)):
        upper_line = lines[index].upper()

        if upper_line in STOP_MARKERS:
            return index

    return len(lines)


def extract_lunch_lines(lines: list[str]) -> list[str]:
    start_index = find_real_lunch_start(lines)

    if start_index is None:
        return []

    end_index = find_lunch_end(lines, start_index)

    return lines[start_index:end_index]


def find_week_range(lines: list[str]) -> str | None:
    for line in lines:
        if looks_like_week_range(line):
            return clean_text(line)

    return None


def find_price_text(lines: list[str]) -> str | None:
    for line in lines:
        lower = line.lower()

        if "tagessuppe" in lower and "€" in line:
            return clean_text(line)

    return None


def find_serving_time(lines: list[str]) -> str | None:
    for line in lines:
        lower = line.lower()

        if "werktags" in lower and "11:30" in line:
            return clean_text(line)

    return None


def find_weekly_vegetarian_special(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if not line.upper().startswith("VEGETARISCHES MENÜ"):
            continue

        special_lines = [clean_text(line)]

        for next_line in lines[index + 1:]:
            cleaned = clean_text(next_line)

            if not cleaned:
                continue

            upper_line = cleaned.upper()

            if upper_line in STOP_MARKERS:
                break

            # Wix artifact from the image/section anchor. Not real menu text.
            if cleaned.lower() == "menue":
                break

            special_lines.append(cleaned)

        return " ".join(line for line in special_lines if line)

    return None


def parse_day_sections(lines: list[str]) -> dict[str, list[str]]:
    sections = {weekday: [] for weekday in WEEKDAYS}
    current_weekday = None

    for line in lines:
        cleaned = clean_text(line)

        if not cleaned:
            continue

        upper_line = cleaned.upper()

        if upper_line in STOP_MARKERS:
            break

        if upper_line.startswith("VEGETARISCHES MENÜ"):
            break

        if upper_line in GERMAN_WEEKDAY_TO_KEY:
            current_weekday = GERMAN_WEEKDAY_TO_KEY[upper_line]
            continue

        if current_weekday is None:
            continue

        lower_line = cleaned.lower()

        # Skip section metadata.
        if upper_line == "MITTAGSMENÜS":
            continue

        if looks_like_week_range(cleaned):
            continue

        if "werktags" in lower_line:
            continue

        if "tagessuppe" in lower_line and "€" in cleaned:
            continue

        sections[current_weekday].append(cleaned)

    return sections


def parse_menu_items(day_lines: list[str]) -> list[MenuItem]:
    """
    Esterházystüberl structure:
    - first line is usually soup
    - remaining one or two lines are the main dish + description

    Example:
    [
      "Gegrillte Hühnerstreifen",
      "auf sommerlichem Salat"
    ]
    becomes:
    name = "Gegrillte Hühnerstreifen"
    description = "auf sommerlichem Salat"
    """
    items = []

    if not day_lines:
        return items

    soup = clean_text(day_lines[0])

    if soup:
        items.append(
            MenuItem(
                name=soup,
                description=None,
                price=None,
                tags=["SOUP"] if "suppe" in soup.lower() else [],
            )
        )

    main_lines = [clean_text(line) for line in day_lines[1:] if clean_text(line)]

    if main_lines:
        main_name = main_lines[0]
        main_description = " ".join(main_lines[1:]) if len(main_lines) > 1 else None

        items.append(
            MenuItem(
                name=main_name,
                description=main_description,
                price=None,
                tags=[],
            )
        )

    return items


def parse_esterhazykeller_menu() -> RestaurantMenu:
    warnings = []

    page_text = fetch_page_text()
    lines = clean_lines(page_text)

    with open("esterhazykeller_raw_lines.txt", "w", encoding="utf-8") as debug_file:
        for index, line in enumerate(lines):
            debug_file.write(f"{index:03}: {line}\n")

    lunch_lines = extract_lunch_lines(lines)

    if not lunch_lines:
        warnings.append("Could not find real Mittagsmenüs section.")
        lunch_lines = lines

    week_range_text = find_week_range(lunch_lines)
    base_price_text = find_price_text(lunch_lines)
    serving_time = find_serving_time(lunch_lines)
    vegetarian_special = find_weekly_vegetarian_special(lunch_lines)

    price_text = base_price_text
    weekly_specials = []

    if vegetarian_special:
        weekly_specials.append(vegetarian_special)

    raw_day_sections = parse_day_sections(lunch_lines)

    days = {}

    for weekday in WEEKDAYS:
        items = parse_menu_items(raw_day_sections.get(weekday, []))

        days[weekday] = DayMenu(
            weekday=weekday,
            label=WEEKDAY_LABELS[weekday],
            items=items,
        )

        if not items:
            warnings.append(f"No menu items found for {weekday}.")

    if not week_range_text:
        warnings.append("Could not detect week range.")

    if not base_price_text:
        warnings.append("Could not detect price text.")

    if not serving_time:
        warnings.append("Could not detect serving time.")

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
        menu_type="weekly_lunch_menu_html",
        week_range_text=week_range_text,
        price_text=price_text,
        serving_time=serving_time,
        current_day=get_current_menu_day(),
        days=days,
        meta=meta,
        notes=[],
        weekly_specials=weekly_specials,
    )


def main():
    menu = parse_esterhazykeller_menu()
    menu_dict = menu.to_dict()

    print(json.dumps(menu_dict, ensure_ascii=False, indent=2))

    with open("esterhazykeller_menu.json", "w", encoding="utf-8") as file:
        json.dump(menu_dict, file, ensure_ascii=False, indent=2)

    print("\nSaved:")
    print("- esterhazykeller_menu.json")
    print("- esterhazykeller_raw_lines.txt")


if __name__ == "__main__":
    main()