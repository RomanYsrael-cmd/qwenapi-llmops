"""FastAPI application factory with auth applied consistently to API routes."""

from __future__ import annotations

import secrets
from typing import Any

from .config import Settings


def create_app(settings: Settings | None = None):
    """Create the HTTP gateway.

    FastAPI is a runtime dependency, so importing the core package remains
    possible in lightweight test environments.
    """

    try:
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Install requirements.txt to run the HTTP gateway") from exc

    cfg = settings or Settings.from_env()
    app = FastAPI(title="QwenAPI Gateway", version="0.1.0")

    def authorize(authorization: str | None) -> bool:
        return bool(
            cfg.api_key
            and authorization
            and secrets.compare_digest(authorization, f"Bearer {cfg.api_key}")
        )

    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next):
        # Keep only the liveness probe public. Every API, stream, image, and
        # documentation route is protected by this single guard.
        if request.url.path != "/health" and not authorize(request.headers.get("authorization")):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", **cfg.public_summary()}

    @app.get("/v1/models")
    async def models() -> dict[str, Any]:
        return {"object": "list", "data": [{"id": cfg.model_name, "object": "model"}]}

    @app.post("/v1/chat/completions")
    async def completions(request: Request) -> JSONResponse:
        payload = await request.json()
        if not isinstance(payload.get("messages"), list):
            raise HTTPException(status_code=422, detail="messages must be a list")
        # The clean repository intentionally keeps the backend adapter pluggable.
        return JSONResponse(
            {
                "id": "demo-not-configured",
                "object": "chat.completion",
                "model": cfg.model_name,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "Backend adapter not configured in this demo."}, "finish_reason": "stop"}],
                "x_qwen_gateway": {"backend_count": len(cfg.qwen_backends)},
            }
        )

    return app
