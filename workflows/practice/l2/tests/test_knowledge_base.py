from workflows.practice.l2.models import KnowledgeBaseArticle
from workflows.practice.l2.tools.knowledge_base import search_kb


def test_search_kb_returns_relevant_articles_ranked():
    results = search_kb("VPN keeps disconnecting")

    assert results
    assert all(isinstance(a, KnowledgeBaseArticle) for a in results)
    assert all("vpn" in a.tags for a in results)


def test_search_kb_respects_limit():
    assert len(search_kb("email", limit=2)) == 2


def test_search_kb_no_match_returns_empty():
    assert search_kb("zzzqqq") == []


def test_search_kb_blank_query_returns_empty():
    assert search_kb("   ") == []
