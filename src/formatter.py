import html

from .models import RestaurantMenu, DayMenu, MenuItem


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