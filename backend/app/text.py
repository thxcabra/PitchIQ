"""Text helpers shared across the data and NLU layers."""
from __future__ import annotations

import unicodedata


def deaccent(s: str) -> str:
    """Strip diacritics: 'Türkiye' -> 'Turkiye'."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))


def normalize(s: str) -> str:
    """Accent-, case- and punctuation-insensitive key for matching names."""
    cleaned = deaccent(s).lower().replace("-", " ").replace(".", " ")
    return " ".join(cleaned.split())
