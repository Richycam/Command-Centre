from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import requests

from geo import GeoIndex
from classifiers import DEFAULT_CLASSIFIER


def _default_user_agent() -> str:
    import platform
    os_name = platform.system()
    match os_name:
        case "Windows":
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        case "Darwin":
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        case "Linux":
            return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        case _:
            return "Mozilla/5.0 (compatible; CommandCentre/1.0; +https://example.com)"


DEFAULT_FEED_HEADERS = {
    "User-Agent": _default_user_agent(),
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class NewsSource:
    key: str
    label: str
    feed_urls: tuple[str, ...]
    headers: Optional[dict[str, str]] = None


NEWS_SOURCES: list[NewsSource] = [
    NewsSource(
        "bbc", "BBC World News",
        ("http://feeds.bbci.co.uk/news/world/rss.xml", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ),
    NewsSource(
        "reuters", "Reuters Top News",
        ("http://feeds.reuters.com/reuters/topNews", "https://feeds.reuters.com/reuters/topNews"),
    ),
    NewsSource(
        "aljazeera", "Al Jazeera",
        ("https://www.aljazeera.com/xml/rss/all.xml",),
    ),
    NewsSource(
        "hn", "Hacker News (Security/Tech)",
        ("https://hnrss.org/frontpage",),
    ),
    NewsSource(
        "nyt", "NY Times World",
        ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml",),
    ),
    NewsSource(
        "reuters_business", "Reuters Business",
        ("http://feeds.reuters.com/reuters/businessNews",),
    ),
    NewsSource(
        "cnn", "CNN World",
        (
            "http://rss.cnn.com/rss/edition_world.rss",
            "http://rss.cnn.com/rss/cnn_world.rss",
            "https://rss.cnn.com/rss/edition_world.rss",
        ),
    ),
    NewsSource(
        "ap", "AP Top News",
        (
            "https://apnews.com/index.rss",
            "https://apnews.com/apf-topnews?format=rss",
            "https://apnews.com/hub/ap-top-news?format=rss",
        ),
    ),
    NewsSource(
        "guardian", "The Guardian World",
        (
            "https://www.theguardian.com/world/rss",
        ),
    ),
    NewsSource(
        "guardian_business", "The Guardian Business",
        (
            "https://www.theguardian.com/business/rss",
        ),
    ),
    NewsSource(
        "ft", "Financial Times",
        (
            "https://www.ft.com/?format=rss",
            "https://www.ft.com/world?format=rss",
        ),
    ),
    NewsSource(
        "bloomberg", "Bloomberg",
        (
            "https://www.bloomberg.com/feed/podcast/etf-report.xml",
        ),
    ),
    NewsSource(
        "cnbc", "CNBC Markets",
        (
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        ),
    ),
    NewsSource(
        "marketwatch", "MarketWatch Top Stories",
        (
            "https://www.marketwatch.com/rss/topstories",
        ),
    ),
    NewsSource(
        "wsj", "WSJ Top Stories",
        (
            "https://www.wsj.com/xml/rss/3_7014.xml",
        ),
    ),
    NewsSource(
        "dw", "DW News World",
        (
            "https://rss.dw.com/xml/DW_World",
        ),
    ),
]


@dataclass
class NewsEvent:
    title: str
    source: str
    lat: float
    lon: float
    category: "EventCategory"
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None
    target_name: Optional[str] = None
    published: str = ""


class NewsFeed:
    def __init__(self, source: NewsSource):
        self.source = source

    @staticmethod
    def _is_recent(entry, days: int = 1) -> bool:
        raw = getattr(entry, "published", None)
        if not raw:
            return True
        try:
            published_date = parsedate_to_datetime(raw).date()
            return published_date >= date.today() - timedelta(days=days)
        except Exception:
            return True

    @staticmethod
    def _entry_text(entry) -> str:
        parts = [
            getattr(entry, "title", ""),
            getattr(entry, "summary", ""),
            getattr(entry, "description", ""),
        ]
        if hasattr(entry, "tags"):
            parts.extend(getattr(tag, "term", "") for tag in getattr(entry, "tags", []))
        return " ".join(str(p) for p in parts if p).lower()

    def _fetch_feed_entries(self) -> list:
        for url in self.source.feed_urls:
            headers = self.source.headers or DEFAULT_FEED_HEADERS
            try:
                response = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
                if response.status_code == 200:
                    parsed = feedparser.parse(response.content)
                    if parsed.entries:
                        return parsed.entries
            except Exception:
                pass

            try:
                parsed = feedparser.parse(url)
                if parsed.entries:
                    return parsed.entries
            except Exception:
                pass

        return []

    def fetch(self, days: int = 2, limit: int = 50) -> list[NewsEvent]:
        events: list[NewsEvent] = []
        parsed_entries = self._fetch_feed_entries()
        if not parsed_entries:
            return events

        recent = [e for e in parsed_entries if self._is_recent(e, days)]
        pool = recent if recent else parsed_entries

        for entry in pool[:limit]:
            title = getattr(entry, "title", "Untitled")
            entry_text = self._entry_text(entry)
            hits = GeoIndex.find_all(entry_text)
            if not hits:
                continue
            origin_name, lat, lon = hits[0]
            category = DEFAULT_CLASSIFIER.classify(entry_text)

            target_name = target_lat = target_lon = None
            if category == "military":
                move = DEFAULT_CLASSIFIER.find_movement(entry_text, origin_name)
                if move:
                    target_name, target_lat, target_lon = move

            events.append(NewsEvent(
                title=title, source=self.source.label, lat=lat, lon=lon,
                category=category, target_lat=target_lat, target_lon=target_lon,
                target_name=target_name, published=getattr(entry, "published", ""),
            ))
        return events


class FeedManager:
    """Higher-level manager that wraps multiple `NewsSource` entries and
    provides convenient methods to fetch and aggregate events. Keeps the
    fetching logic centralized for easier testing and future caching.
    """

    def __init__(self, sources: list[NewsSource] | None = None):
        self.sources = sources or NEWS_SOURCES

    def list_sources(self) -> list[tuple[str, str]]:
        return [(s.key, s.label) for s in self.sources]

    def fetch(self, source_key: str, days: int = 2, limit: int = 50) -> list[NewsEvent]:
        source = next((s for s in self.sources if s.key == source_key), None)
        if not source:
            return []
        return NewsFeed(source).fetch(days=days, limit=limit)

    def fetch_all(self, days: int = 2, limit_per_source: int = 50) -> list[NewsEvent]:
        events: list[NewsEvent] = []
        for s in self.sources:
            events.extend(NewsFeed(s).fetch(days=days, limit=limit_per_source))
        # Simple dedupe based on title+lat+lon
        seen = set()
        unique: list[NewsEvent] = []
        for e in events:
            key = (e.title, round(e.lat, 3), round(e.lon, 3))
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)
        return unique
