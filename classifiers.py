from __future__ import annotations

from enum import Enum
from typing import Optional


class EventCategory(str, Enum):
    MILITARY = "military"
    POLITICAL = "political"
    FINANCIAL = "financial"
    DISASTER = "disaster"
    GENERAL = "general"


CATEGORY_COLOR: dict[EventCategory, str] = {
    EventCategory.MILITARY: "#ff3b3b",
    EventCategory.POLITICAL: "#ffd23b",
    EventCategory.FINANCIAL: "#3bff8a",
    EventCategory.DISASTER: "#c93bff",
    EventCategory.GENERAL: "#3bc9ff",
}
CATEGORY_SYMBOL: dict[EventCategory, str] = {
    EventCategory.MILITARY: "triangle-up",
    EventCategory.POLITICAL: "square",
    EventCategory.FINANCIAL: "diamond",
    EventCategory.DISASTER: "x",
    EventCategory.GENERAL: "circle-open",
}

MILITARY_KEYWORDS = [
    "invasion", "invades", "strike", "strikes", "offensive", "clash",
    "clashes", "troops", "military", "airstrike", "missile", "war",
    "attack", "attacks", "shelling", "combat", "forces", "defense",
    "defence", "drone", "nuclear", "ceasefire", "troop", "battle",
    "artillery", "naval", "militia", "insurgency", "rebels", "rebellion",
    "occupation", "security", "border", "terrorist", "terrorism",
    "martial", "siege", "ambush", "rocket", "munition",
]
DISASTER_KEYWORDS = [
    "earthquake", "flood", "hurricane", "wildfire", "tsunami", "eruption",
    "storm", "cyclone", "heatwave", "drought", "blizzard", "landslide",
    "avalanche", "volcano", "mudslide", "blackout", "power outage",
    "evacuation", "pandemic", "outbreak", "epidemic", "virus", "disease",
    "contamination", "spill", "pollution", "tornado", "snowstorm",
    "ice storm", "landslide", "extreme weather", "collapse",
]
FINANCIAL_KEYWORDS = [
    "stocks", "shares", "dow", "nasdaq", "sp500", "s&p 500", "market", "markets",
    "earnings", "revenue", "profit", "loss", "merger", "acquisition", "ipo",
    "inflation", "interest rate", "rate hike", "fed", "reserve", "central bank",
    "bond", "yield", "currency", "crypto", "bitcoin", "ethereum", "financial",
    "bank", "banking", "federal reserve", "ftse", "dax", "nikkei", "oil price",
    "commodity", "gold", "silver", "cpi", "gdp", "economic", "economy",
    "budget", "deficit", "bailout", "liquidity", "credit", "debt",
    "exchange", "trading", "stock market", "bullish", "bearish", "bankrupt",
    "housing market", "real estate", "lender", "loan", "mortgage", "interest",
    "investment", "capital", "venture", "private equity", "hedge fund",
    "corporate", "earnings report", "margin", "asset", "liability",
    "savings", "pension", "inflationary", "restructuring", "dividend",
]

POLITICAL_KEYWORDS = [
    "election", "president", "parliament", "summit", "sanctions", "treaty",
    "government", "minister", "prime minister", "policy", "diplomacy",
    "legislation", "debate", "campaign", "vote", "referendum", "congress",
    "senate", "assembly", "coalition", "demonstration", "coup", "protest",
    "rally", "strike", "cabinet", "budget", "tariff", "trade",
    "immigration", "foreign minister", "reform", "judicial", "court",
    "judge", "law", "negotiation", "diplomatic", "parliamentary",
]


class EventClassifier:
    """Instance-based classifier so keyword sets can be injected or
    swapped for testing.
    """

    def __init__(self,
                 military_keywords: list[str] | None = None,
                 disaster_keywords: list[str] | None = None,
                 financial_keywords: list[str] | None = None,
                 political_keywords: list[str] | None = None):
        self.military_keywords = military_keywords or MILITARY_KEYWORDS
        self.disaster_keywords = disaster_keywords or DISASTER_KEYWORDS
        self.financial_keywords = financial_keywords or FINANCIAL_KEYWORDS
        self.political_keywords = political_keywords or POLITICAL_KEYWORDS

    def classify(self, title: str) -> EventCategory:
        text = title.lower()
        if any(k in text for k in self.military_keywords):
            return EventCategory.MILITARY
        if any(k in text for k in self.disaster_keywords):
            return EventCategory.DISASTER
        if any(k in text for k in self.financial_keywords):
            return EventCategory.FINANCIAL
        if any(k in text for k in self.political_keywords):
            return EventCategory.POLITICAL
        return EventCategory.GENERAL

    def find_movement(self, title: str, origin_name: str) -> Optional[tuple[str, float, float]]:
        from geo import GeoIndex
        for name, lat, lon in GeoIndex.find_all(title):
            if name != origin_name:
                return name, lat, lon
        return None


DEFAULT_CLASSIFIER = EventClassifier()
