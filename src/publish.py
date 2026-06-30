import os
import traceback

from .confluence_client import ConfluenceClient
from .formatter import format_confluence_lunch_page
from .restaurants.wienerin import parse_wienerin_menu
from .restaurants.wrenkh import parse_wrenkh_menu


def safe_parse_restaurant(name: str, parser_func):
    try:
        return parser_func(), None
    except Exception:
        return None, f"{name} failed"


def get_enabled_restaurants() -> set[str]:
    raw_value = os.getenv("ENABLED_RESTAURANTS")

    if not raw_value:
        return {"wrenkh", "wienerin"}

    return {
        item.strip().lower()
        for item in raw_value.split(",")
        if item.strip()
    }


def build_markdown_output() -> str:
    enabled_restaurants = get_enabled_restaurants()

    available_parser_jobs = {
        "wrenkh": ("WRENKH", parse_wrenkh_menu),
        "wienerin": ("Wienerin", parse_wienerin_menu),
    }

    menus = []
    errors = []

    for key, parser_job in available_parser_jobs.items():
        if key not in enabled_restaurants:
            continue

        restaurant_name, parser_func = parser_job
        menu, error = safe_parse_restaurant(restaurant_name, parser_func)

        if menu:
            menus.append(menu)

        if error:
            errors.append(error)

    return format_confluence_lunch_page(
        menus=menus,
        errors=errors,
    )


def main():
    markdown_output = build_markdown_output()

    with open("lunch_menus.md", "w", encoding="utf-8") as file:
        file.write(markdown_output)

    client = ConfluenceClient()
    result = client.update_page_from_markdown(markdown_output)

    print("Confluence page updated.")
    print(f"Page ID: {result['id']}")
    print(f"Title: {result['title']}")
    print(f"Version: {result['version']['number']}")


if __name__ == "__main__":
    main()