from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.utils.masking_utils import is_empty

KANNADA_TRAFFIC_GLOSSARY = {
    "ಜಂಕ್ಷನ್": "junction",
    "ರಸ್ತೆ": "road",
    "ಅಪಘಾತ": "accident",
    "ಮಳೆ": "rain",
    "ನೀರು": "water",
    "ಸಂಚಾರ": "traffic",
    "ವಾಹನ": "vehicle",
    "ಭಾರಿ": "heavy",
    "ನಿಧಾನ": "slow",
    "ಮರ": "tree",
}


@dataclass(frozen=True)
class NormalizedDescription:
    raw: str | None
    language: str
    text_for_features: str | None
    method: str
    confidence: float


def detect_description_language(value: Any) -> str:
    if is_empty(value):
        return "unknown"

    text = str(value)
    kannada_chars = sum(1 for char in text if "\u0C80" <= char <= "\u0CFF")
    devanagari_chars = sum(1 for char in text if "\u0900" <= char <= "\u097F")
    ascii_letters = sum(1 for char in text if char.isascii() and char.isalpha())

    if (kannada_chars or devanagari_chars) and ascii_letters:
        return "mixed"
    if kannada_chars:
        return "kn"
    if devanagari_chars:
        return "hi"
    return "en"


def _ascii_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalize_description(value: Any) -> NormalizedDescription:
    if is_empty(value):
        return NormalizedDescription(None, "unknown", None, "empty", 0.0)

    raw = str(value).strip()
    language = detect_description_language(raw)

    if language == "en":
        return NormalizedDescription(raw, "en", " ".join(_ascii_tokens(raw)), "raw_ascii", 0.95)

    mapped_terms = [
        english for kannada, english in KANNADA_TRAFFIC_GLOSSARY.items() if kannada in raw
    ]
    ascii_terms = _ascii_tokens(raw) if language == "mixed" else []
    combined_terms = list(dict.fromkeys(mapped_terms + ascii_terms))

    if combined_terms:
        method = "static_kannada_glossary" if mapped_terms else "mixed_ascii_preserved"
        confidence = 0.6 if mapped_terms else 0.35
        return NormalizedDescription(
            raw=raw,
            language=language,
            text_for_features=" ".join(combined_terms),
            method=method,
            confidence=confidence,
        )

    return NormalizedDescription(raw, language, None, "skipped_low_confidence", 0.0)
