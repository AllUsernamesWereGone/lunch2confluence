from src.restaurants.wienerin import parse_wienerin_menu


def test_wienerin_returns_restaurant_metadata():
    menu = parse_wienerin_menu()

    assert menu.restaurant.id == "wienerin"
    assert menu.restaurant.name == "Wienerin"
    assert menu.restaurant.address == "Petersplatz 1, 1010 Wien"
    assert menu.restaurant.source_url.endswith(".pdf")


def test_wienerin_returns_all_weekdays():
    menu = parse_wienerin_menu()

    assert set(menu.days.keys()) == {"MO", "DI", "MI", "DO", "FR"}


def test_wienerin_has_menu_items_for_at_least_one_day():
    menu = parse_wienerin_menu()

    total_items = sum(len(day_menu.items) for day_menu in menu.days.values())

    assert total_items > 0


def test_wienerin_detects_week_range():
    menu = parse_wienerin_menu()

    assert menu.week_range_text is not None
    assert "bis" in menu.week_range_text.lower()


def test_wienerin_items_have_clean_structure():
    menu = parse_wienerin_menu()

    all_items = [
        item
        for day_menu in menu.days.values()
        for item in day_menu.items
    ]

    assert len(all_items) > 0

    for item in all_items:
        assert item.name is not None
        assert item.name.strip() != ""