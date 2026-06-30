from .confluence_client import ConfluenceClient
from .formatter import format_restaurant_menu_markdown
from .restaurants.wienerin import parse_wienerin_menu
from .restaurants.wrenkh import parse_wrenkh_menu


def build_markdown_output() -> str:
    menus = [
        parse_wrenkh_menu(),
        parse_wienerin_menu(),
    ]

    markdown_parts = [
        "# Lunch Menus",
        "",
        "Automatically generated lunch menu overview.",
        "",
    ]

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