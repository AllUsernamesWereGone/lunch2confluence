import html
from datetime import datetime
from zoneinfo import ZoneInfo
from .models import RestaurantMenu, DayMenu, MenuItem

WEEKDAY_ORDER = ["MO", "DI", "MI", "DO", "FR"]

def format_menu_item(item: MenuItem) -> str:
    name = clean_output(item.name)
    description = clean_output(item.description)
    price = clean_output(item.price)

    title = f"- **{name}**"

    if price:
        title += f" — {price}"

    parts = [title]

    if description:
        parts.append(f"  {description}")

    if item.tags:
        tags = ", ".join(item.tags)
        parts.append(f"  _{tags}_")

    return "\n".join(parts)


def format_day_menu(day_menu: DayMenu) -> str:
    lines = [
        f"## {day_menu.weekday} - {day_menu.label}",
        "",
    ]

    if not day_menu.items:
        lines.append("_No menu found._")
        return "\n".join(lines)

    for item in day_menu.items:
        lines.append(format_menu_item(item))
        lines.append("")

    return "\n".join(lines).strip()

def clean_output(value: str | None) -> str:
    if value is None:
        return ""

    return html.unescape(value).replace("\xa0", " ").strip()

def format_restaurant_menu_markdown(menu: RestaurantMenu) -> str:
    lines = [
        f"# {menu.restaurant.name} Lunch Menu",
        "",

        f"**Address:** {clean_output(menu.restaurant.address)}",
        f"**Source:** {clean_output(menu.restaurant.source_url)}",

    ]

    if menu.week_range_text:
        lines.append(f"**Week:** {clean_output(menu.week_range_text)}")

    if menu.price_text:
        lines.append(f"**Price:** {clean_output(menu.price_text)}")

    if menu.serving_time:
        lines.append(f"**Serving time:** {clean_output(menu.serving_time)}")

    lines.append("")

    if menu.current_day and menu.current_day in menu.days:
        lines.append("# Today")
        lines.append("")
        lines.append(format_day_menu(menu.days[menu.current_day]))
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("# Full Week")
    lines.append("")

    for weekday in ["MO", "DI", "MI", "DO", "FR"]:
        if weekday in menu.days:
            lines.append(format_day_menu(menu.days[weekday]))
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Fetched at: {menu.meta.fetched_at}_")

    if menu.meta.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in menu.meta.warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines).strip()




def table_cell(value: str | None) -> str:
    """
    Escapes text so it behaves nicely inside Markdown tables.
    """
    cleaned = clean_output(value)

    if not cleaned:
        return ""

    return cleaned.replace("|", "\\|").replace("\n", "<br>")


def format_menu_item_compact(item: MenuItem) -> str:
    name = table_cell(item.name)
    description = table_cell(item.description)
    price = table_cell(getattr(item, "price", None))

    parts = []

    title = f"<strong>{name}</strong>"

    if price:
        title += f" — {price}"

    parts.append(title)

    if description:
        parts.append(description)

    if item.tags:
        tags = ", ".join(item.tags)
        parts.append(f"<em>{table_cell(tags)}</em>")

    return "<br>".join(parts)


def format_day_items_for_table(day_menu: DayMenu | None) -> str:
    if day_menu is None or not day_menu.items:
        return ""

    return "<br><br>".join(
        format_menu_item_compact(item)
        for item in day_menu.items
    )


def get_weekly_special(menu: RestaurantMenu) -> str:
    """
    Returns whole-week special notes.

    For now, Wienerin's price_text contains the soup/salad/daily soup notes.
    Wrenkh's price_text is just general pricing, so we do not treat it as a special.
    """
    price_text = clean_output(menu.price_text)

    if not price_text:
        return ""

    restaurant_id = menu.restaurant.id.lower()

    if restaurant_id == "wienerin":
        return price_text

    if "tagessuppe" in price_text.lower() or "täglich" in price_text.lower():
        return price_text

    return ""


def get_restaurant_notes(menu: RestaurantMenu) -> str:
    notes = []

    if menu.serving_time:
        notes.append(clean_output(menu.serving_time))

    # Wrenkh's price text is general pricing, useful for today's table notes.
    weekly_special = get_weekly_special(menu)

    if menu.price_text and clean_output(menu.price_text) != weekly_special:
        notes.append(clean_output(menu.price_text))

    return "<br>".join(table_cell(note) for note in notes if note)


def format_today_table(menus: list[RestaurantMenu]) -> str:
    lines = [
        "## Today",
        "",
        "| Restaurant | Today's menu | Notes |",
        "|---|---|---|",
    ]

    for menu in menus:
        current_day = menu.current_day
        day_menu = menu.days.get(current_day) if current_day else None

        restaurant = table_cell(menu.restaurant.name)
        today_items = format_day_items_for_table(day_menu)
        notes = get_restaurant_notes(menu)

        lines.append(f"| {restaurant} | {today_items} | {notes} |")

    return "\n".join(lines)


def format_week_table(menus: list[RestaurantMenu]) -> str:
    lines = [
        "## Full week",
        "",
        "| Restaurant | Weekly special | MO | DI | MI | DO | FR |",
        "|---|---|---|---|---|---|---|",
    ]

    for menu in menus:
        restaurant = table_cell(menu.restaurant.name)
        weekly_special = table_cell(get_weekly_special(menu))

        day_cells = []

        for weekday in WEEKDAY_ORDER:
            day_menu = menu.days.get(weekday)
            day_cells.append(format_day_items_for_table(day_menu))

        lines.append(
            f"| {restaurant} | {weekly_special} | "
            f"{day_cells[0]} | {day_cells[1]} | {day_cells[2]} | {day_cells[3]} | {day_cells[4]} |"
        )

    return "\n".join(lines)


def format_errors(errors: list[str]) -> str:
    lines = [
        "## Errors",
        "",
    ]

    if not errors:
        lines.append("_No errors._")
        return "\n".join(lines)

    for error in errors:
        lines.append(f"- {table_cell(error)}")

    return "\n".join(lines)


def format_confluence_lunch_page(
    menus: list[RestaurantMenu],
    errors: list[str],
) -> str:
    pulled_at = datetime.now(
        ZoneInfo("Europe/Vienna")
    ).strftime("%d.%m.%Y %H:%M:%S Europe/Vienna")

    lines = [
        "# Lunch Menus",
        "",
        f"**Pulled at:** {pulled_at}",
        "",
    ]

    if menus:
        lines.append(format_today_table(menus))
        lines.append("")
        lines.append(format_week_table(menus))
        lines.append("")
    else:
        lines.extend(
            [
                "## Today",
                "",
                "_No restaurant menus could be fetched._",
                "",
            ]
        )

    lines.append(format_errors(errors))

    return "\n".join(lines)
