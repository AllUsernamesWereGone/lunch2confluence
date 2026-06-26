import json

from .restaurants.wrenkh import parse_wrenkh_menu


def main():
    menus = [
        parse_wrenkh_menu(),
    ]

    output = [menu.to_dict() for menu in menus]

    print(json.dumps(output, ensure_ascii=False, indent=2))

    with open("lunch_menus.json", "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()