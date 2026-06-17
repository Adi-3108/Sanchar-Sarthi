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
    "ಟ್ರಾಫಿಕ್": "traffic",
    "ಜಾಮ್": "jam",
    "ವಾಹನ": "vehicle",
    "ಭಾರಿ": "heavy",
    "ನಿಧಾನ": "slow",
    "ಮರ": "tree",
}

HINDI_TRAFFIC_GLOSSARY = {
    "चौराहा": "junction",
    "जंक्शन": "junction",
    "सड़क": "road",
    "रास्ता": "road",
    "दुर्घटना": "accident",
    "हादसा": "accident",
    "बारिश": "rain",
    "पानी": "water",
    "ट्रैफिक": "traffic",
    "यातायात": "traffic",
    "जाम": "jam",
    "वाहन": "vehicle",
    "भारी": "heavy",
    "धीमा": "slow",
    "पेड़": "tree",
    "भीड़": "crowd",
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


def _mapped_glossary_terms(text: str, language: str) -> list[str]:
    glossaries = []
    if language in {"kn", "mixed"}:
        glossaries.append(KANNADA_TRAFFIC_GLOSSARY)
    if language in {"hi", "mixed"}:
        glossaries.append(HINDI_TRAFFIC_GLOSSARY)

    mapped_terms: list[str] = []
    for glossary in glossaries:
        mapped_terms.extend(english for source, english in glossary.items() if source in text)
    return mapped_terms


def normalize_description(value: Any) -> NormalizedDescription:
    if is_empty(value):
        return NormalizedDescription(None, "unknown", None, "empty", 0.0)

    raw = str(value).strip()
    language = detect_description_language(raw)

    if language == "en":
        return NormalizedDescription(raw, "en", " ".join(_ascii_tokens(raw)), "raw_ascii", 0.95)

    mapped_terms = _mapped_glossary_terms(raw, language)
    ascii_terms = _ascii_tokens(raw) if language == "mixed" else []
    combined_terms = list(dict.fromkeys(mapped_terms + ascii_terms))

    if combined_terms:
        if language == "kn" and mapped_terms:
            method = "static_kannada_glossary"
        elif language == "hi" and mapped_terms:
            method = "static_hindi_glossary"
        elif mapped_terms:
            method = "static_multilingual_glossary"
        else:
            method = "mixed_ascii_preserved"
        confidence = 0.6 if mapped_terms else 0.35
        return NormalizedDescription(
            raw=raw,
            language=language,
            text_for_features=" ".join(combined_terms),
            method=method,
            confidence=confidence,
        )

    return NormalizedDescription(raw, language, None, "skipped_low_confidence", 0.0)
