from src.restaurants.wien1bezirk.wienerin import parse_wienerin_menu
from src.restaurants.wien1bezirk.wrenkh import parse_wrenkh_menu
from src.restaurants.wien1bezirk.esterhazystueberl import parse_esterhazykeller_menu


AVAILABLE_RESTAURANTS = {
    # "example_restaurant": {
    #     "display_name": "Example Restaurant",
    #     "parser": parse_example_restaurant_menu,
    # },

    "wrenkh": {
        "display_name": "Wrenkh",
        "parser": parse_wrenkh_menu,
    },
    "wienerin": {
        "display_name": "Wienerin",
        "parser": parse_wienerin_menu,
    },

    "esterhazykeller": {
        "display_name": "Esterházystüberl",
        "parser": parse_esterhazykeller_menu,
    },

}