import os

from .formatter import format_confluence_lunch_page
from .restaurants.registry import AVAILABLE_RESTAURANTS


def parse_restaurant_env_list(variable_name: str) -> set[str]:
    raw_value = os.getenv(variable_name)

    if raw_value is None or not raw_value.strip():
        return set()

    return {
        item.strip().lower()
        for item in raw_value.split(",")
        if item.strip()
    }


def get_enabled_restaurants() -> set[str]:
    enabled_restaurants = parse_restaurant_env_list("ENABLED_RESTAURANTS")
    disabled_restaurants = parse_restaurant_env_list("DISABLED_RESTAURANTS")

    if not enabled_restaurants:
        selected_restaurants = set(AVAILABLE_RESTAURANTS.keys())
    else:
        selected_restaurants = enabled_restaurants

    return selected_restaurants - disabled_restaurants


def safe_parse_restaurant(
    restaurant_key: str,
    display_name: str,
    parser_func,
):
    try:
        menu = parser_func()

        returned_id = menu.restaurant.id.lower().strip()
        expected_id = restaurant_key.lower().strip()

        print(
            f"[INFO] Parsed restaurant: "
            f"registry_key={restaurant_key}, "
            f"display_name={display_name}, "
            f"returned_id={menu.restaurant.id}, "
            f"returned_name={menu.restaurant.name}"
        )

        if returned_id != expected_id:
            return None, (
                f"{display_name} failed: parser returned id "
                f"'{returned_id}' instead of expected id '{expected_id}'"
            )

        return menu, None

    except Exception as error:
        print(f"[ERROR] {display_name} failed: {error}")
        return None, f"{display_name} failed"


def collect_menus():
    enabled_restaurants = get_enabled_restaurants()

    menus = []
    errors = []

    for restaurant_key, restaurant_config in AVAILABLE_RESTAURANTS.items():
        if restaurant_key not in enabled_restaurants:
            continue

        menu, error = safe_parse_restaurant(
            restaurant_key=restaurant_key,
            display_name=restaurant_config["display_name"],
            parser_func=restaurant_config["parser"],
        )

        if menu:
            menus.append(menu)

        if error:
            errors.append(error)

    return menus, errors


def build_confluence_page_html() -> str:
    menus, errors = collect_menus()

    return format_confluence_lunch_page(
        menus=menus,
        errors=errors,
    )