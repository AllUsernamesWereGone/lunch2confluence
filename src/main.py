from .menu_builder import build_confluence_page_html


def main():
    html_output = build_confluence_page_html()

    with open("lunch_menus.html", "w", encoding="utf-8") as file:
        file.write(html_output)

    print(html_output)
    print("\nSaved to lunch_menus.html")


if __name__ == "__main__":
    main()