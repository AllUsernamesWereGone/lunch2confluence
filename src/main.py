import json

from .restaurants.wrenkh import parse_wrenkh_menu
from .formatter import format_restaurant_menu_markdown


def main():
    menu = parse_wrenkh_menu()

    # JSON output
    menu_dict = menu.to_dict()

    with open("wrenkh_menu.json", "w", encoding="utf-8") as json_file:
        json.dump(menu_dict, json_file, ensure_ascii=False, indent=2)

    # Markdown/text output
    markdown_output = format_restaurant_menu_markdown(menu)

    print(markdown_output)

    with open("wrenkh_menu.md", "w", encoding="utf-8") as markdown_file:
        markdown_file.write(markdown_output)

    print("\nSaved:")
    print("- wrenkh_menu.json")
    print("- wrenkh_menu.md")


if __name__ == "__main__":
    main()
