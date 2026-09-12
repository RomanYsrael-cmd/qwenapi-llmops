"""Grounding policy classification for agentic requests."""

from __future__ import annotations

from dataclasses import dataclass
import re


_CATEGORIES: dict[str, tuple[str, ...]] = {
    "legal": ("legal", "law", "regulation", "statute", "civil code", "court"),
    "medical": ("medical", "diagnosis", "symptom", "medicine", "dosage"),
    "financial": ("investment", "stock", "tax", "loan", "exchange rate", "finance"),
    "cybersecurity": ("malware", "ransomware", "vulnerability", "cve", "phishing"),
    "government": ("government", "official requirement", "visa", "permit", "tesda"),
    "public_safety": ("recall", "emergency", "earthquake", "typhoon", "public safety"),
}


@dataclass(frozen=True)
class Classification:
    category: str
    policy: str
    reason: str
    mandatory: bool


def classify_query(query: str, grounding_mode: str = "smart") -> Classification:
    """Classify a request and choose a fail-safe grounding policy.

    ``smart`` is the default.  High-stakes categories always require live
    evidence, even when a caller asks for grounding to be disabled.
    """

    text = query.casefold()
    category = "general"
    for candidate, keywords in _CATEGORIES.items():
        if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
            category = candidate
            break

    mandatory = category in {"legal", "medical", "financial", "cybersecurity", "government", "public_safety"}
    normalized = grounding_mode.casefold().strip()
    if normalized not in {"smart", "auto", "required", "off", "source_only"}:
        normalized = "required"  # unknown modes fail safe

    if mandatory:
        return Classification(category, "required", "mandatory_high_stakes", True)
    if normalized == "source_only":
        return Classification(category, "source_only", "caller_requested_source_only", False)
    if normalized == "off":
        return Classification(category, "off", "caller_disabled_grounding", False)
    if normalized == "required":
        return Classification(category, "required", "caller_requested_grounding", False)
    return Classification(category, "smart", "default_policy", False)
