import json

from .formatter import format_restaurant_menu_markdown
from .restaurants.wienerin import parse_wienerin_menu
from .restaurants.wrenkh import parse_wrenkh_menu


def main():
    menus = [
        parse_wrenkh_menu(),
        parse_wienerin_menu(),
    ]

    menu_dicts = [menu.to_dict() for menu in menus]

    with open("lunch_menus.json", "w", encoding="utf-8") as json_file:
        json.dump(menu_dicts, json_file, ensure_ascii=False, indent=2)

    markdown_parts = []

    for menu in menus:
        markdown_parts.append(format_restaurant_menu_markdown(menu))

    markdown_output = "\n\n---\n\n".join(markdown_parts)

    print(markdown_output)

    with open("lunch_menus.md", "w", encoding="utf-8") as markdown_file:
        markdown_file.write(markdown_output)

    print("\nSaved:")
    print("- lunch_menus.json")
    print("- lunch_menus.md")


if __name__ == "__main__":
    main()