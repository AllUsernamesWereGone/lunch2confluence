from .confluence_client import ConfluenceClient
from .menu_builder import build_confluence_page_html


def main():
    html_output = build_confluence_page_html()

    with open("lunch_menus.html", "w", encoding="utf-8") as file:
        file.write(html_output)

    client = ConfluenceClient()
    result = client.update_page_from_markdown(html_output)

    print("Confluence page updated.")
    print(f"Page ID: {result['id']}")
    print(f"Title: {result['title']}")
    print(f"Version: {result['version']['number']}")


if __name__ == "__main__":
    main()