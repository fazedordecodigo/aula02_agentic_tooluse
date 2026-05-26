from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter


def normalize_text(text: str) -> str:
    """Normaliza texto para matching determinístico em português."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [tok for tok in normalized.split() if len(tok) >= 2]


def cosine_similarity(a: str, b: str) -> float:
    """Cosseno simples com bag-of-words para fallback offline."""
    ca = Counter(tokenize(a))
    cb = Counter(tokenize(b))
    if not ca or not cb:
        return 0.0
    common = set(ca) & set(cb)
    numerator = sum(ca[t] * cb[t] for t in common)
    denom_a = math.sqrt(sum(v * v for v in ca.values()))
    denom_b = math.sqrt(sum(v * v for v in cb.values()))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return round(numerator / (denom_a * denom_b), 4)


def contains_any(text: str, terms: list[str]) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(term) in normalized for term in terms)
