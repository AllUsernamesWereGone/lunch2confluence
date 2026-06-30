from src.restaurants.wien1bezirk.wrenkh import parse_wrenkh_menu


def test_wrenkh_returns_restaurant_metadata():
    menu = parse_wrenkh_menu()

    assert menu.restaurant.id == "wrenkh"
    assert menu.restaurant.name == "Wrenkh"
    assert menu.restaurant.address == "Bauernmarkt 10, 1010 Wien"
    assert menu.restaurant.source_url.startswith("https://")


def test_wrenkh_returns_all_weekdays():
    menu = parse_wrenkh_menu()

    assert set(menu.days.keys()) == {"MO", "DI", "MI", "DO", "FR"}


def test_wrenkh_has_menu_items_for_at_least_one_day():
    menu = parse_wrenkh_menu()

    total_items = sum(len(day_menu.items) for day_menu in menu.days.values())

    assert total_items > 0


def test_wrenkh_does_not_include_footer_as_menu_item():
    menu = parse_wrenkh_menu()

    all_item_names = [
        item.name
        for day_menu in menu.days.values()
        for item in day_menu.items
    ]

    assert "Restaurant Bauernmarkt" not in all_item_names
    assert "Kontakt & Impressum" not in all_item_names