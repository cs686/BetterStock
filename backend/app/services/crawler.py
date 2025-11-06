"""Asynchronous news crawler implementation."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterable, List

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NewsItem:
    source: str
    title: str
    url: str
    published_at: datetime
    summary: str
    content: str
    payload: Dict[str, Any]


class BaseSource:
    name: str

    async def fetch(self, session: aiohttp.ClientSession) -> AsyncIterator[NewsItem]:
        raise NotImplementedError


class RSSSource(BaseSource):
    """Generic RSS source fetcher."""

    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self._url = url

    async def fetch(self, session: aiohttp.ClientSession) -> AsyncIterator[NewsItem]:
        async with session.get(self._url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            text = await response.text()
        soup = BeautifulSoup(text, "xml")
        for item in soup.find_all("item")[:20]:
            link = item.link.text if item.link else ""
            pub_date = item.pubDate.text if item.pubDate else ""
            published_at = (
                datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").astimezone()
                if pub_date
                else datetime.utcnow()
            )
            description = item.description.text if item.description else ""
            content = description
            yield NewsItem(
                source=self.name,
                title=item.title.text if item.title else "",
                url=link,
                published_at=published_at,
                summary=description[:200],
                content=content,
                payload={"raw": item.text},
            )


class HtmlListSource(BaseSource):
    """Source scraping simple HTML list pages."""

    def __init__(self, name: str, url: str, item_selector: str) -> None:
        self.name = name
        self._url = url
        self._selector = item_selector

    async def fetch(self, session: aiohttp.ClientSession) -> AsyncIterator[NewsItem]:
        async with session.get(self._url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            text = await response.text()
        soup = BeautifulSoup(text, "html.parser")
        for element in soup.select(self._selector)[:20]:
            link = element.get("href") or self._url
            title = element.text.strip()
            yield NewsItem(
                source=self.name,
                title=title,
                url=link,
                published_at=datetime.utcnow(),
                summary=title,
                content=title,
                payload={"raw": element.attrs},
            )


class NewsCrawler:
    def __init__(self, sources: Iterable[BaseSource]) -> None:
        self.sources = list(sources)

    async def crawl(self) -> List[NewsItem]:
        results: List[NewsItem] = []
        async with aiohttp.ClientSession(headers={"User-Agent": "BetterStockBot/1.0"}) as session:
            tasks = [self._fetch_source(session, source) for source in self.sources]
            for task in asyncio.as_completed(tasks):
                try:
                    items = await task
                    results.extend(items)
                except Exception as exc:  # pragma: no cover - network errors
                    logger.exception("Failed to crawl source: %s", exc)
        return results

    async def _fetch_source(self, session: aiohttp.ClientSession, source: BaseSource) -> List[NewsItem]:
        items: List[NewsItem] = []
        async for item in source.fetch(session):
            items.append(item)
        return items


DEFAULT_SOURCES: List[BaseSource] = [
    RSSSource("东方财富", "https://finance.eastmoney.com/rss/stock.xml"),
    RSSSource("新浪财经", "https://rss.sina.com.cn/finance/stock/cnstocknews.xml"),
]


async def fetch_latest_news() -> List[NewsItem]:
    crawler = NewsCrawler(DEFAULT_SOURCES)
    return await crawler.crawl()
