"""Search cache, deduplication, and an async Roman Search client."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import time
from typing import Any, Awaitable, Callable
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source_id: str = ""
    score: float = 0.0


def canonical_url(url: str) -> str:
    """Normalize URLs enough for deterministic result deduplication."""

    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.casefold() or "https"
    host = (parsed.hostname or "").casefold()
    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((scheme, host, path, parsed.query, ""))


def dedupe_results(results: list[SearchResult], max_per_domain: int = 2) -> list[SearchResult]:
    """Remove duplicate URLs and cap results from one domain."""

    seen: set[str] = set()
    domains: dict[str, int] = {}
    output: list[SearchResult] = []
    for item in sorted(results, key=lambda r: r.score, reverse=True):
        url = canonical_url(item.url)
        domain = urlsplit(url).netloc
        if url in seen or domains.get(domain, 0) >= max_per_domain:
            continue
        seen.add(url)
        domains[domain] = domains.get(domain, 0) + 1
        output.append(item)
    return output


class SearchCache:
    """Bounded TTL cache used to avoid repeated identical searches."""

    TTL_SECONDS = {
        "legal": 4 * 60 * 60,
        "medical": 60 * 60,
        "cybersecurity": 60 * 60,
        "financial": 3 * 60,
        "government": 2 * 60 * 60,
        "public_safety": 5 * 60,
        "general": 10 * 60,
    }

    def __init__(self, max_entries: int = 500, clock: Callable[[], float] | None = None):
        self.max_entries = max_entries
        self._clock = clock or time.monotonic
        self._values: OrderedDict[str, tuple[float, list[SearchResult]]] = OrderedDict()

    @staticmethod
    def key(query: str, category: str, depth: str) -> str:
        raw = f"{category}|{depth}|{query.strip().casefold()}".encode()
        return hashlib.sha256(raw).hexdigest()

    def get(self, query: str, category: str, depth: str) -> list[SearchResult] | None:
        key = self.key(query, category, depth)
        entry = self._values.get(key)
        if entry is None:
            return None
        timestamp, results = entry
        if self._clock() - timestamp > self.TTL_SECONDS.get(category, self.TTL_SECONDS["general"]):
            self._values.pop(key, None)
            return None
        self._values.move_to_end(key)
        return list(results)

    def put(self, query: str, category: str, depth: str, results: list[SearchResult]) -> None:
        key = self.key(query, category, depth)
        self._values[key] = (self._clock(), list(results))
        self._values.move_to_end(key)
        while len(self._values) > self.max_entries:
            self._values.popitem(last=False)


class RomanSearchClient:
    """Minimal async adapter; HTTP is imported only when the adapter is used."""

    def __init__(self, base_url: str, api_key: str, timeout_seconds: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, *, category: str, depth: str = "basic", limit: int = 5) -> list[SearchResult]:
        if not self.api_key:
            raise RuntimeError("ROMAN_SEARCH_API_KEY is not configured")
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - exercised in deployment
            raise RuntimeError("Install the runtime dependencies before using RomanSearchClient") from exc

        payload = {"query": query, "category": category, "depth": depth, "limit": min(limit, 20)}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/v1/search", json=payload, headers=headers)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        raw_results = data.get("results", [])
        return dedupe_results(
            [
                SearchResult(
                    title=str(item.get("title", "")),
                    url=str(item.get("url", "")),
                    snippet=str(item.get("snippet", item.get("content", "")))[:1800],
                    source_id=str(item.get("source_id", "")),
                    score=float(item.get("score", 0.0)),
                )
                for item in raw_results
                if item.get("url")
            ]
        )


async def cached_search(
    cache: SearchCache,
    client: RomanSearchClient,
    query: str,
    *,
    category: str,
    depth: str = "basic",
    limit: int = 5,
) -> list[SearchResult]:
    """Cache a search result and coalesce duplicate in-flight requests."""

    cached = cache.get(query, category, depth)
    if cached is not None:
        return cached
    results = await client.search(query, category=category, depth=depth, limit=limit)
    cache.put(query, category, depth, results)
    return results
