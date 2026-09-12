"""Async round-robin adapter for local OpenAI-compatible model workers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BackendReply:
    status_code: int
    payload: dict[str, Any]
    backend: str


class BackendUnavailable(RuntimeError):
    """Raised when every configured model worker is unavailable."""


class BackendPool:
    """Round-robin pool with bounded connection timeouts.

    The pool deliberately does not own or spawn llama.cpp processes. That
    lifecycle belongs to the deployment layer (Kaggle, systemd, or a job
    runner), which keeps this module easy to test and reuse.
    """

    def __init__(self, endpoints: list[str], timeout_seconds: float = 180.0):
        self.endpoints = [endpoint.rstrip("/") for endpoint in endpoints if endpoint.strip()]
        self.timeout_seconds = timeout_seconds
        self._cursor = 0
        self._lock = asyncio.Lock()

    async def _ordered_endpoints(self) -> list[str]:
        async with self._lock:
            if not self.endpoints:
                return []
            start = self._cursor % len(self.endpoints)
            self._cursor += 1
            return self.endpoints[start:] + self.endpoints[:start]

    async def chat(self, payload: dict[str, Any], authorization: str | None = None) -> BackendReply:
        endpoints = await self._ordered_endpoints()
        if not endpoints:
            raise BackendUnavailable("No model backends are configured")
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - deployment guard
            raise BackendUnavailable("Install the runtime dependencies before using the backend pool") from exc

        headers = {"Authorization": authorization} if authorization else {}
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for endpoint in endpoints:
                try:
                    response = await client.post(
                        f"{endpoint}/v1/chat/completions", json=payload, headers=headers
                    )
                    data = response.json()
                    return BackendReply(response.status_code, data, endpoint)
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = exc
        raise BackendUnavailable(f"All model backends failed: {last_error}")
