from .wienerin import parse_wienerin_menu
from .wrenkh import parse_wrenkh_menu


AVAILABLE_RESTAURANTS = {
    # "example_restaurant": {
    #     "display_name": "Example Restaurant",
    #     "parser": parse_example_restaurant_menu,
    # },

    "wrenkh": {
        "display_name": "WRENKH",
        "parser": parse_wrenkh_menu,
    },
    "wienerin": {
        "display_name": "Wienerin",
        "parser": parse_wienerin_menu,
    },
}