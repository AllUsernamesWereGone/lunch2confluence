import traceback

from .confluence_client import ConfluenceClient
from .formatter import format_restaurant_menu_markdown
from .restaurants.wienerin import parse_wienerin_menu
from .restaurants.wrenkh import parse_wrenkh_menu


def safe_parse_restaurant(name: str, parser_func):
    try:
        return parser_func(), None
    except Exception as error:
        warning = {
            "restaurant": name,
            "error": str(error),
            "traceback": traceback.format_exc(),
        }
        return None, warning


def build_markdown_output() -> str:
    parser_jobs = [
        ("WRENKH", parse_wrenkh_menu),
        ("Wienerin", parse_wienerin_menu),
    ]

    menus = []
    warnings = []

    for restaurant_name, parser_func in parser_jobs:
        menu, warning = safe_parse_restaurant(restaurant_name, parser_func)

        if menu:
            menus.append(menu)

        if warning:
            warnings.append(warning)

    markdown_parts = [
        "# Lunch Menus",
        "",
        "Automatically generated lunch menu overview.",
        "",
    ]

    if warnings:
        markdown_parts.extend(
            [
                "## Import warnings",
                "",
                "Some restaurant menus could not be fetched during this run.",
                "",
            ]
        )

        for warning in warnings:
            markdown_parts.append(f"- **{warning['restaurant']}**: {warning['error']}")

        markdown_parts.append("")

    if not menus:
        markdown_parts.extend(
            [
                "## No menus available",
                "",
                "No restaurant menus could be fetched during this run.",
                "",
            ]
        )
    else:
        for menu in menus:
            markdown_parts.append(format_restaurant_menu_markdown(menu))
            markdown_parts.append("")
            markdown_parts.append("---")
            markdown_parts.append("")

    return "\n".join(markdown_parts)


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