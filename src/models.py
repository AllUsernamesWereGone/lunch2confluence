from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class Restaurant:
    id: str
    name: str
    address: Optional[str]
    source_url: str


@dataclass
class MenuItem:
    name: str
    description: Optional[str] = None
    price: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class DayMenu:
    weekday: str
    label: str
    items: list[MenuItem] = field(default_factory=list)


@dataclass
class MenuMeta:
    fetched_at: str
    parser: str
    status: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class RestaurantMenu:
    restaurant: Restaurant
    menu_type: str
    week_range_text: Optional[str]
    price_text: Optional[str]
    serving_time: Optional[str]
    current_day: Optional[str]
    days: dict[str, DayMenu]
    meta: MenuMeta

    def to_dict(self) -> dict:
        return asdict(self)