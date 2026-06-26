from .models import RestaurantMenu, DayMenu, MenuItem


def format_menu_item(item: MenuItem) -> str:
    parts = [f"- **{item.name}**"]

    if item.description:
        parts.append(f"  {item.description}")

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


def format_restaurant_menu_markdown(menu: RestaurantMenu) -> str:
    lines = [
        f"# {menu.restaurant.name} Lunch Menu",
        "",
        f"**Address:** {menu.restaurant.address}",
        f"**Source:** {menu.restaurant.source_url}",
    ]

    if menu.week_range_text:
        lines.append(f"**Week:** {menu.week_range_text}")

    if menu.price_text:
        lines.append(f"**Price:** {menu.price_text}")

    if menu.serving_time:
        lines.append(f"**Serving time:** {menu.serving_time}")

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