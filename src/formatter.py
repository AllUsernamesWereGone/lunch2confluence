import html
from datetime import datetime
from zoneinfo import ZoneInfo

from .models import RestaurantMenu, DayMenu, MenuItem


WEEKDAY_ORDER = ["MO", "DI", "MI", "DO", "FR"]

WEEKDAY_DISPLAY = {
    "MO": "Monday",
    "DI": "Tuesday",
    "MI": "Wednesday",
    "DO": "Thursday",
    "FR": "Friday",
}


def clean_output(value: str | None) -> str:
    if value is None:
        return ""

    return html.unescape(str(value)).replace("\xa0", " ").strip()


def html_text(value: str | None) -> str:
    return html.escape(clean_output(value))


def format_menu_item(item: MenuItem) -> str:
    """
    Legacy Markdown formatter, still useful for tests/local markdown output.
    """
    name = clean_output(item.name)
    description = clean_output(item.description)
    price = clean_output(getattr(item, "price", None))

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
    """
    Legacy Markdown formatter, still useful for tests/local markdown output.
    """
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
    """
    Legacy Markdown formatter.
    Your Confluence page now uses the HTML formatter below.
    """
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

    for weekday in WEEKDAY_ORDER:
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


def format_item_html(item: MenuItem) -> str:
    name = html_text(item.name)
    description = html_text(item.description)
    price = html_text(getattr(item, "price", None))

    title = f"<strong>{name}</strong>"

    if price:
        title += f" — {price}"

    parts = [title]

    if description:
        parts.append(description)

    if item.tags:
        tags = ", ".join(item.tags)
        parts.append(f"<em>{html_text(tags)}</em>")

    return "<br />".join(parts)


def format_day_menu_html(day_menu: DayMenu | None) -> str:
    if day_menu is None or not day_menu.items:
        return "<em>No menu found.</em>"

    return "<br /><br />".join(
        format_item_html(item)
        for item in day_menu.items
    )




def get_weekly_specials(menu: RestaurantMenu) -> list[str]:
    return [
        clean_output(special)
        for special in menu.weekly_specials
        if clean_output(special)
    ]


def get_restaurant_notes(menu: RestaurantMenu) -> str:
    notes = []

    if menu.serving_time:
        notes.append(clean_output(menu.serving_time))

    if menu.price_text:
        notes.append(clean_output(menu.price_text))

    notes.extend(menu.notes)

    return "<br />".join(html_text(note) for note in notes if note)


def confluence_expand_macro(title: str, body_html: str) -> str:
    return f"""
    <ac:structured-macro ac:name="expand">
        <ac:parameter ac:name="title">{html_text(title)}</ac:parameter>
        <ac:rich-text-body>
            {body_html}
        </ac:rich-text-body>
    </ac:structured-macro>
    """


def format_today_restaurant_block_html(menu: RestaurantMenu) -> str:
    current_day = menu.current_day
    day_menu = menu.days.get(current_day) if current_day else None
    notes = get_restaurant_notes(menu)

    return f"""
    <h3>{html_text(menu.restaurant.name)}</h3>
    <table>
        <thead>
            <tr>
                <th>Today's menu</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{format_day_menu_html(day_menu)}</td>
                <td>{notes}</td>
            </tr>
        </tbody>
    </table>
    """


def format_today_section_html(menus: list[RestaurantMenu]) -> str:
    if not menus:
        return """
        <h2>Today</h2>
        <p><em>No restaurant menus could be fetched.</em></p>
        """

    sections = [
        "<h2>Today</h2>"
    ]

    for menu in menus:
        sections.append(format_today_restaurant_block_html(menu))

    return "\n".join(sections)


def format_restaurant_week_table_html(menu: RestaurantMenu) -> str:
    rows = []

    weekly_specials = get_weekly_specials(menu)

    if weekly_specials:
        rows.append(
            f"""
            <tr>
                <td><strong>Special / whole week</strong></td>
                <td>{"<br />".join(html_text(special) for special in weekly_specials)}</td>
            </tr>
            """
        )

    for weekday in WEEKDAY_ORDER:
        day_menu = menu.days.get(weekday)
        day_label = WEEKDAY_DISPLAY.get(weekday, weekday)

        rows.append(
            f"""
            <tr>
                <td><strong>{weekday}</strong><br />{html_text(day_label)}</td>
                <td>{format_day_menu_html(day_menu)}</td>
            </tr>
            """
        )

    return f"""
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Menu</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def format_restaurant_week_section_html(menu: RestaurantMenu) -> str:
    table_html = format_restaurant_week_table_html(menu)

    return confluence_expand_macro(
        title=f"{menu.restaurant.name} - full week",
        body_html=table_html,
    )


def format_full_week_section_html(menus: list[RestaurantMenu]) -> str:
    sections = [
        "<h2>Full week</h2>"
    ]

    for menu in menus:
        sections.append(format_restaurant_week_section_html(menu))

    return "\n".join(sections)


def format_errors_section_html(errors: list[str]) -> str:
    if not errors:
        return """
        <h2>Errors</h2>
        <p><em>No errors.</em></p>
        """

    error_items = "".join(
        f"<li>{html_text(error)}</li>"
        for error in errors
    )

    return f"""
    <h2>Errors</h2>
    <ul>
        {error_items}
    </ul>
    """


def format_confluence_lunch_page(
    menus: list[RestaurantMenu],
    errors: list[str],
) -> str:
    pulled_at = datetime.now(
        ZoneInfo("Europe/Vienna")
    ).strftime("%d.%m.%Y %H:%M:%S Europe/Vienna")

    return f"""
    <h1>Lunch Menus</h1>

    <p><strong>Pulled at:</strong> {html_text(pulled_at)}</p>

    {format_today_section_html(menus)}

    {format_full_week_section_html(menus)}

    {format_errors_section_html(errors)}
    """
