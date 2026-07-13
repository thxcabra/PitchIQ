"""
News for players / teams / competitions.

Uses the Google News RSS search feed — free, no API key. Results are cached in-memory
with a short TTL so a page load doesn't hammer the feed, and any failure degrades
gracefully to an empty list (the UI simply hides the section).
"""
from __future__ import annotations

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

_TTL_SECONDS = 1800  # 30 min


@dataclass
class NewsItem:
    title: str
    link: str
    source: str | None
    published: str | None


class NewsService:
    def __init__(self, timeout: float = 8.0):
        self._timeout = timeout
        self._cache: dict[str, tuple[float, list[NewsItem]]] = {}

    def search(self, query: str, limit: int = 6) -> list[NewsItem]:
        key = query.strip().lower()
        hit = self._cache.get(key)
        if hit and (time.time() - hit[0]) < _TTL_SECONDS:
            return hit[1][:limit]

        items = self._fetch(query)
        self._cache[key] = (time.time(), items)
        return items[:limit]

    def _fetch(self, query: str) -> list[NewsItem]:
        q = urllib.parse.quote(f"{query} football")
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pitchiq/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                root = ET.fromstring(r.read())
        except Exception:  # noqa: BLE001 - any failure -> no news, never breaks the page
            return []

        out: list[NewsItem] = []
        for it in root.findall(".//item"):
            title = it.findtext("title") or ""
            link = it.findtext("link") or ""
            src_el = it.find("{*}source")
            out.append(NewsItem(
                title=title.strip(),
                link=link.strip(),
                source=src_el.text if src_el is not None else None,
                published=it.findtext("pubDate"),
            ))
        return out
