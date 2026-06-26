from src.formatter import format_restaurant_menu_markdown
from src.restaurants.wrenkh import parse_wrenkh_menu
from src.restaurants.wienerin import parse_wienerin_menu


def test_formatter_outputs_wrenkh_markdown():
    menu = parse_wrenkh_menu()
    output = format_restaurant_menu_markdown(menu)

    assert isinstance(output, str)
    assert "WRENKH" in output
    assert "Lunch Menu" in output
    assert "Full Week" in output


def test_formatter_outputs_wienerin_markdown():
    menu = parse_wienerin_menu()
    output = format_restaurant_menu_markdown(menu)

    assert isinstance(output, str)
    assert "Wienerin" in output
    assert "Lunch Menu" in output
    assert "Full Week" in output


def test_formatter_does_not_output_html_entities():
    menus = [
        parse_wrenkh_menu(),
        parse_wienerin_menu(),
    ]

    output = "\n\n".join(
        format_restaurant_menu_markdown(menu)
        for menu in menus
    )

    assert "&amp;" not in output
    assert "&nbsp;" not in output