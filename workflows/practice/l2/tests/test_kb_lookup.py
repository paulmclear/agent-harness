import pytest

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.models import (
    KnowledgeBaseArticle,
    SupportCategory,
    SupportTicket,
)
from workflows.practice.l2.nodes import kb_lookup_node as node_module
from workflows.practice.l2.nodes.kb_lookup_node import build_kb_query, kb_lookup_node


@pytest.fixture
def vpn_state():
    return {
        "ticket": SupportTicket(
            ticket_id="T100",
            employee_id="E001",
            subject="Can't connect from home",
            description="The client says connection failed every time I try.",
        ),
        "ticket_category": SupportCategory.vpn,
    }


@pytest.fixture
def recorded_search(monkeypatch):
    calls: list[dict] = []

    def fake_search_kb(query: str, limit: int) -> list[KnowledgeBaseArticle]:
        calls.append({"query": query, "limit": limit})
        return []

    monkeypatch.setattr(node_module, "search_kb", fake_search_kb)
    return calls


def test_query_combines_subject_description_and_category(vpn_state):
    query = build_kb_query(vpn_state["ticket"], vpn_state["ticket_category"])

    assert query == (
        "Can't connect from home "
        "The client says connection failed every time I try. "
        "vpn"
    )


def test_calls_search_once_with_configured_limit(vpn_state, recorded_search):
    kb_lookup_node(vpn_state)

    assert len(recorded_search) == 1
    assert recorded_search[0]["limit"] == get_settings().kb_lookup_limit


def test_category_boosts_matching_articles(vpn_state):
    # Ticket text never says "vpn"; the category term pulls VPN articles up via tags.
    result = kb_lookup_node(vpn_state)

    candidates = result["kb_candidates"]
    assert candidates
    assert all(isinstance(a, KnowledgeBaseArticle) for a in candidates)
    assert candidates[0].article_id.startswith("kb-vpn-")


def test_no_match_returns_empty_candidates(recorded_search):
    state = {
        "ticket": SupportTicket(
            ticket_id="T101", employee_id="E001", subject="zzzqqq", description=""
        ),
        "ticket_category": SupportCategory.other,
    }

    assert kb_lookup_node(state) == {"kb_candidates": []}
