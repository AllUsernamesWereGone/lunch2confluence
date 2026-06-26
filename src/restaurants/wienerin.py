import datetime
import html
import io
import json
import re
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import pdfplumber
import requests
from bs4 import BeautifulSoup

from ..models import Restaurant, MenuItem, DayMenu, MenuMeta, RestaurantMenu


PAGE_URL = "https://wienerin.org/speisen.html"
FALLBACK_PDF_URL = "https://wienerin.org/wienerin_tagesteller.pdf"

WEEKDAYS = ["MO", "DI", "MI", "DO", "FR"]

WEEKDAY_LABELS = {
    "MO": "Monday",
    "DI": "Tuesday",
    "MI": "Wednesday",
    "DO": "Thursday",
    "FR": "Friday",
}

PYTHON_WEEKDAY_TO_WIENERIN = {
    0: "MO",
    1: "DI",
    2: "MI",
    3: "DO",
    4: "FR",
}

GERMAN_WEEKDAY_TO_KEY = {
    "montag": "MO",
    "dienstag": "DI",
    "mittwoch": "MI",
    "donnerstag": "DO",
    "freitag": "FR",
}


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


def fetch_pdf_url() -> str:
    try:
        response = requests.get(PAGE_URL, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            link_text = link.get_text(" ", strip=True).lower()

            if "tagesteller" in href.lower() and href.lower().endswith(".pdf"):
                return urljoin(PAGE_URL, href)

            if "mittag" in link_text and href.lower().endswith(".pdf"):
                return urljoin(PAGE_URL, href)

    except requests.RequestException:
        pass

    return FALLBACK_PDF_URL


def download_pdf(pdf_url: str) -> bytes:
    response = requests.get(pdf_url, timeout=20)
    response.raise_for_status()
    return response.content


def extract_pdf_text(pdf_content: bytes) -> str:
    extracted_pages = []

    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            extracted_pages.append(page_text)

    return "\n".join(extracted_pages)


def find_week_range(lines: list[str]) -> str | None:
    pattern = re.compile(
        r"von\s+\d{1,2}\.\d{1,2}\.\d{4}\s+bis\s+\d{1,2}\.\d{1,2}\.\d{4}",
        re.IGNORECASE,
    )

    for line in lines:
        match = pattern.search(line)
        if match:
            return match.group(0)

    return None


def find_soup_and_salad(lines: list[str]) -> str | None:
    for line in lines:
        cleaned = clean_text(line)

        if cleaned and "Tagessuppe" in cleaned and "Backhendlsalat" in cleaned:
            return cleaned

    return None


def find_daily_soup_note(lines: list[str]) -> str | None:
    for line in lines:
        cleaned = clean_text(line)

        if cleaned and cleaned.lower().startswith("täglich:"):
            return cleaned

    return None


def parse_price_from_text(text: str) -> tuple[str, str | None]:
    """
    Splits:
    'Kirschtomate - Rucola € 12,00'
    into:
    ('Kirschtomate - Rucola', '€ 12,00')
    """
    match = re.search(r"(€\s*\d+,\d{2})", text)

    if not match:
        return text, None

    price = match.group(1)
    without_price = text.replace(price, "").strip()

    return without_price, price


def parse_day_heading(line: str) -> tuple[str, str] | None:
    """
    Parses:
    'Montag: Spargelpasta'
    into:
    ('MO', 'Spargelpasta')
    """
    if ":" not in line:
        return None

    weekday_part, dish_part = line.split(":", 1)

    weekday_key = GERMAN_WEEKDAY_TO_KEY.get(weekday_part.lower().strip())

    if not weekday_key:
        return None

    dish_name = clean_text(dish_part)

    if not dish_name:
        return None

    return weekday_key, dish_name


def parse_wienerin_days(lines: list[str]) -> dict[str, DayMenu]:
    days = {
        weekday: DayMenu(
            weekday=weekday,
            label=WEEKDAY_LABELS[weekday],
            items=[],
        )
        for weekday in WEEKDAYS
    }

    index = 0

    while index < len(lines):
        line = lines[index]
        parsed_heading = parse_day_heading(line)

        if not parsed_heading:
            index += 1
            continue

        weekday, main_dish = parsed_heading

        description = None
        price = None

        # Wienerin PDF layout: next line usually contains side/sauce + price.
        if index + 1 < len(lines):
            next_line = clean_text(lines[index + 1])

            # Only consume next line if it is not another weekday heading and not a generic note.
            if (
                next_line
                and not parse_day_heading(next_line)
                and not next_line.lower().startswith("täglich:")
                and "gutschein" not in next_line.lower()
                and "liebe geht" not in next_line.lower()
            ):
                description_without_price, price = parse_price_from_text(next_line)
                description = description_without_price
                index += 1

        if price:
            description_text = f"{description} ({price})" if description else price
        else:
            description_text = description

        days[weekday].items.append(
            MenuItem(
                name=main_dish,
                description=description_text,
                tags=[],
            )
        )

        index += 1

    return days


def get_current_wienerin_day() -> str | None:
    today = datetime.date.today()
    return PYTHON_WEEKDAY_TO_WIENERIN.get(today.weekday())


def parse_wienerin_menu() -> RestaurantMenu:
    warnings = []

    pdf_url = fetch_pdf_url()
    pdf_content = download_pdf(pdf_url)
    pdf_text = extract_pdf_text(pdf_content)

    lines = clean_lines(pdf_text)

    # Helpful while developing. Keep ignored in .gitignore.
    with open("wienerin_raw_lines.txt", "w", encoding="utf-8") as debug_file:
        for index, line in enumerate(lines):
            debug_file.write(f"{index:03}: {line}\n")

    week_range_text = find_week_range(lines)
    soup_and_salad = find_soup_and_salad(lines)
    daily_soup_note = find_daily_soup_note(lines)

    price_parts = []

    if soup_and_salad:
        price_parts.append(soup_and_salad)

    if daily_soup_note:
        price_parts.append(daily_soup_note)

    price_text = " | ".join(price_parts) if price_parts else None

    days = parse_wienerin_days(lines)

    current_day = get_current_wienerin_day()

    if not week_range_text:
        warnings.append("Could not detect week range.")

    if not any(day.items for day in days.values()):
        warnings.append("Could not detect any weekday menu items.")

    fetched_at = datetime.datetime.now(
        ZoneInfo("Europe/Vienna")
    ).isoformat(timespec="seconds")

    restaurant = Restaurant(
        id="wienerin",
        name="Wienerin",
        address="Petersplatz 1, 1010 Wien",
        source_url=pdf_url,
    )

    meta = MenuMeta(
        fetched_at=fetched_at,
        parser="wienerin",
        status="success",
        warnings=warnings,
    )

    return RestaurantMenu(
        restaurant=restaurant,
        menu_type="weekly_lunch_menu_pdf",
        week_range_text=week_range_text,
        price_text=price_text,
        serving_time=None,
        current_day=current_day,
        days=days,
        meta=meta,
    )


def main():
    menu = parse_wienerin_menu()
    menu_dict = menu.to_dict()

    print(json.dumps(menu_dict, ensure_ascii=False, indent=2))

    with open("wienerin_menu.json", "w", encoding="utf-8") as file:
        json.dump(menu_dict, file, ensure_ascii=False, indent=2)

    print("\nSaved to wienerin_menu.json")


if __name__ == "__main__":
    main()