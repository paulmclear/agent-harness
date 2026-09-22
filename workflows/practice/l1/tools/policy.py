"""Internal knowledge base — keyword-overlap search over ``data/policies.yaml``."""

import re

from workflows.practice.l1.tools._data import load
from workflows.practice.l1.tools.models import PolicyChunk

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def search_policy_tool(query: str, top_k: int = 3) -> list[PolicyChunk]:
    """Return the ``top_k`` policy chunks sharing the most terms with ``query``.

    Score is the fraction of query terms present in the chunk (title + text).
    Chunks with no overlap are excluded.
    """
    query_terms = _tokens(query)
    if not query_terms:
        return []

    scored = []
    for record in load("policies.yaml"):
        chunk_terms = _tokens(f"{record['title']} {record['text']}")
        overlap = len(query_terms & chunk_terms)
        if overlap:
            scored.append(PolicyChunk(**record, score=overlap / len(query_terms)))

    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_k]
