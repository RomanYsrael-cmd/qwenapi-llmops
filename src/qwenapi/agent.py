"""Small agentic orchestration layer independent of the model runtime."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Any, Protocol

from .policy import Classification, classify_query
from .search import SearchCache, SearchResult, cached_search


class LLMBackend(Protocol):
    async def complete(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]: ...


class SearchProvider(Protocol):
    async def search(self, query: str, *, category: str, depth: str = "basic", limit: int = 5) -> list[SearchResult]: ...


@dataclass
class AgentResponse:
    content: str
    classification: Classification
    search_calls: int
    sources: list[SearchResult]
    elapsed_seconds: float
    safeguard_triggered: bool = False


class AgentRunner:
    """Run bounded, source-aware search/tool turns around a chat backend."""

    def __init__(
        self,
        backend: LLMBackend,
        search_provider: SearchProvider,
        *,
        cache: SearchCache | None = None,
        max_runtime_seconds: int = 900,
        max_search_calls: int = 12,
    ):
        self.backend = backend
        self.search_provider = search_provider
        self.cache = cache or SearchCache()
        self.max_runtime_seconds = max_runtime_seconds
        self.max_search_calls = max_search_calls

    async def run(self, messages: list[dict[str, str]], grounding_mode: str = "smart") -> AgentResponse:
        started = time.monotonic()
        query = "\n".join(message.get("content", "") for message in messages[-2:])
        classification = classify_query(query, grounding_mode)
        sources: list[SearchResult] = []
        calls = 0
        safeguard = False
        working = list(messages)
        tools = [{"type": "function", "function": {"name": "web_search", "description": "Find current sources"}}]

        while calls < self.max_search_calls and time.monotonic() - started < self.max_runtime_seconds:
            response = await asyncio.wait_for(self.backend.complete(working, tools=tools), timeout=self.max_runtime_seconds)
            message = response.get("message", response)
            tool_calls = message.get("tool_calls", []) if isinstance(message, dict) else []
            if not tool_calls:
                return AgentResponse(
                    str(message.get("content", "")), classification, calls, sources, time.monotonic() - started, safeguard
                )
            for tool_call in tool_calls:
                if calls >= self.max_search_calls:
                    safeguard = True
                    break
                arguments = tool_call.get("function", {}).get("arguments", {})
                if isinstance(arguments, str):
                    # The production gateway parses JSON; this layer intentionally fails safe.
                    import json
                    arguments = json.loads(arguments)
                search_query = str(arguments.get("query", "")).strip()
                if not search_query:
                    safeguard = True
                    break
                depth = "advanced" if classification.mandatory else "basic"
                sources.extend(
                    await cached_search(self.cache, self.search_provider, search_query, category=classification.category, depth=depth)
                )
                calls += 1
                working.append({"role": "tool", "content": _format_sources(sources)})

        safeguard = True
        response = await self.backend.complete(working, tools=None)
        message = response.get("message", response)
        return AgentResponse(
            str(message.get("content", "")), classification, calls, sources, time.monotonic() - started, safeguard
        )


def _format_sources(sources: list[SearchResult]) -> str:
    return "\n".join(f"[{item.source_id or 'source'}] {item.title} — {item.url}\n{item.snippet}" for item in sources[-20:])
