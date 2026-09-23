import re

from workflows.practice.l2.models import KnowledgeBaseArticle
from workflows.practice.l2.tools._data import load_yaml

# Field weights for naive keyword scoring: tag/title hits count more than body hits.
_FIELD_WEIGHTS = {"tags": 3, "title": 2, "summary": 1, "content": 1}

_STOPWORDS = frozenset(
    "a an and are can cannot do does for from how i in is it my not of on or the to with".split()
)


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


def _score(article: KnowledgeBaseArticle, terms: set[str]) -> int:
    fields = {
        "tags": " ".join(article.tags),
        "title": article.title,
        "summary": article.summary,
        "content": article.content,
    }
    return sum(
        weight * len(terms & _tokenize(fields[name]))
        for name, weight in _FIELD_WEIGHTS.items()
    )


def search_kb(query: str, limit: int = 3) -> list[KnowledgeBaseArticle]:
    """Search the knowledge base for articles matching the query. - Placeholder implementation.

    Naive keyword overlap scoring; a stand-in for real retrieval (BM25 / vector search).

    Args:
        query: Free-text search query, e.g. a ticket subject or description.
        limit: Maximum number of articles to return.

    Returns:
        Matching articles, highest score first. Empty if nothing matches.
    """

    kb = load_yaml("knowledge_base.yaml")
    articles = [KnowledgeBaseArticle(**a) for a in kb["articles"]]

    terms = _tokenize(query)
    if not terms:
        return []

    scored = [(s, a) for a in articles if (s := _score(a, terms)) > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [a for _, a in scored[:limit]]
