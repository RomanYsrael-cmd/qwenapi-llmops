"""Environment-backed configuration with safe defaults.

No credential is stored in code.  Production deployments should inject
secrets through the platform secret store and keep ``.env`` files out of git.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the gateway and demo services."""

    model_name: str = "Qwen3.5-4B"
    context_size: int = 32_768
    max_concurrent_generations: int = 4
    qwen_backends: list[str] = field(default_factory=list)
    fast_backend: str = "http://127.0.0.1:8083"
    image_backend: str = "http://127.0.0.1:8090"
    search_base_url: str = "https://search.romanlms.com"
    search_results: int = 5
    agent_max_runtime_seconds: int = 900
    request_timeout_seconds: float = 180.0
    public_hostname: str = ""
    api_key: str = ""
    roman_search_api_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings without printing or logging sensitive values."""

        return cls(
            model_name=os.getenv("QWEN_MODEL_NAME", cls.model_name),
            context_size=int(os.getenv("QWEN_CONTEXT_SIZE", cls.context_size)),
            max_concurrent_generations=int(
                os.getenv("QWEN_MAX_CONCURRENT", cls.max_concurrent_generations)
            ),
            qwen_backends=_csv(os.getenv("QWEN_BACKENDS", "")),
            fast_backend=os.getenv("QWEN_FAST_BACKEND", cls.fast_backend),
            image_backend=os.getenv("QWEN_IMAGE_BACKEND", cls.image_backend),
            search_base_url=os.getenv("ROMAN_SEARCH_BASE_URL", cls.search_base_url),
            search_results=int(os.getenv("WEB_SEARCH_RESULTS", cls.search_results)),
            agent_max_runtime_seconds=int(
                os.getenv("AGENT_MAX_RUNTIME_SECONDS", cls.agent_max_runtime_seconds)
            ),
            request_timeout_seconds=float(
                os.getenv("QWEN_TURN_TIMEOUT_SECONDS", cls.request_timeout_seconds)
            ),
            public_hostname=os.getenv("PUBLIC_HOSTNAME", ""),
            api_key=os.getenv("QWEN_API_KEY", ""),
            roman_search_api_key=os.getenv("ROMAN_SEARCH_API_KEY", ""),
        )

    def public_summary(self) -> dict[str, object]:
        """Return operational metadata safe for a health response."""

        return {
            "model": self.model_name,
            "context_size": self.context_size,
            "max_concurrent_generations": self.max_concurrent_generations,
            "backend_count": len(self.qwen_backends),
            "search_provider": "Roman Search",
            "search_results": self.search_results,
        }
