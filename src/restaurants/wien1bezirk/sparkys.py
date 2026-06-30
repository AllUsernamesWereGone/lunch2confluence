import datetime
import html
import json
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from src.models import Restaurant, DayMenu, MenuItem, MenuMeta, RestaurantMenu


PAGE_URL = "https://www.sparkys.at/"
SPECIAL_MENU_URL = "https://www.sparkys.at/speisekarte/spezialkarte"

WEEKDAYS = ["MO", "DI", "MI", "DO", "FR"]

WEEKDAY_LABELS = {
    "MO": "Monday",
    "DI": "Tuesday",
    "MI": "Wednesday",
    "DO": "Thursday",
    "FR": "Friday",
}

PYTHON_WEEKDAY_TO_SPARKYS = {
    0: "MO",
    1: "DI",
    2: "MI",
    3: "DO",
    4: "FR",
}

MENU_KEYWORDS = [
    "mittag",
    "mittagsmenü",
    "mittagsmenüs",
    "tagessuppe",
    "tagesmenü",
    "menü",
    "suppe",
]


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    return html.unescape(value).replace("\xa0", " ").strip()


def clean_lines(text: str) -> list[str]:
    lines = []

    for line in text.splitlines():
        cleaned = clean_text(line)

        if cleaned:
            lines.append(cleaned)

    return lines


def fetch_page_text(url: str) -> tuple[str, str | None]:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text("\n", strip=True), None

    except requests.RequestException as error:
        return "", str(error)


def find_menu_related_lines(lines: list[str]) -> list[str]:
    result = []

    for line in lines:
        lower = line.lower()

        if any(keyword in lower for keyword in MENU_KEYWORDS):
            result.append(line)

    return result


def get_current_sparkys_day() -> str | None:
    today = datetime.date.today()
    return PYTHON_WEEKDAY_TO_SPARKYS.get(today.weekday())


def parse_sparkys_menu() -> RestaurantMenu:
    warnings = []

    homepage_text, homepage_error = fetch_page_text(PAGE_URL)
    homepage_lines = clean_lines(homepage_text)

    special_text, special_error = fetch_page_text(SPECIAL_MENU_URL)
    special_lines = clean_lines(special_text)

    if homepage_error:
        warnings.append(f"Could not fetch Sparky's homepage: {homepage_error}")

    if special_error:
        warnings.append(f"Could not fetch Sparky's special menu page: {special_error}")

    with open("sparkys_raw_homepage.txt", "w", encoding="utf-8") as debug_file:
        for index, line in enumerate(homepage_lines):
            debug_file.write(f"{index:03}: {line}\n")

    with open("sparkys_raw_spezialkarte.txt", "w", encoding="utf-8") as debug_file:
        for index, line in enumerate(special_lines):
            debug_file.write(f"{index:03}: {line}\n")

    homepage_menu_lines = find_menu_related_lines(homepage_lines)
    special_menu_lines = find_menu_related_lines(special_lines)

    all_candidate_lines = homepage_menu_lines + special_menu_lines

    days = {
        weekday: DayMenu(
            weekday=weekday,
            label=WEEKDAY_LABELS[weekday],
            items=[],
        )
        for weekday in WEEKDAYS
    }

    current_day = get_current_sparkys_day()

    # For now, only add lines if we find actual-looking content.
    # The official site currently mostly exposes descriptive text, not the daily menu itself.
    actual_menu_lines = [
        line
        for line in all_candidate_lines
        if "3 wechselnde mittagsmenüs" not in line.lower()
        and "frühentschlossenen" not in line.lower()
        and "Loading" not in line
        and "Schnuppert ein wenig" not in line
    ]

    if actual_menu_lines and current_day:
        for line in actual_menu_lines:
            days[current_day].items.append(
                MenuItem(
                    name=clean_text(line),
                    description=None,
                    price=None,
                    tags=[],
                )
            )
    else:
        warnings.append(
            "Could not find actual Sparky's lunch menu content in static HTML. "
            "The menu is probably embedded or loaded dynamically."
        )
        warnings.append(
            "Debug files written: sparkys_raw_homepage.txt and sparkys_raw_spezialkarte.txt."
        )

    fetched_at = datetime.datetime.now(
        ZoneInfo("Europe/Vienna")
    ).isoformat(timespec="seconds")

    restaurant = Restaurant(
        id="sparkys",
        name="Sparky's Unlimited",
        address="Goldschmiedgasse 8, 1010 Wien",
        source_url=PAGE_URL,
    )

    meta = MenuMeta(
        fetched_at=fetched_at,
        parser="sparkys",
        status="partial",
        warnings=warnings,
    )

    return RestaurantMenu(
        restaurant=restaurant,
        menu_type="embedded_or_dynamic_lunch_menu",
        week_range_text=None,
        price_text=None,
        serving_time=None,
        current_day=current_day,
        days=days,
        meta=meta,
    )


def main():
    menu = parse_sparkys_menu()
    menu_dict = menu.to_dict()

    print(json.dumps(menu_dict, ensure_ascii=False, indent=2))

    with open("sparkys_menu.json", "w", encoding="utf-8") as file:
        json.dump(menu_dict, file, ensure_ascii=False, indent=2)

    print("\nSaved to sparkys_menu.json")


if __name__ == "__main__":
    main()