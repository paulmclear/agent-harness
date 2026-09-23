import pytest

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.models import (
    ArticleRelevance,
    GradedArticle,
    SupportCategory,
    SupportPriority,
    SupportTicket,
    TriageDraft,
)
from workflows.practice.l2.nodes.build_triage_output_node import (
    build_triage_output_node,
)


def _graded(article_id: str, relevance: ArticleRelevance) -> GradedArticle:
    return GradedArticle(article_id=article_id, relevance=relevance, confidence=0.9)


@pytest.fixture(autouse=True)
def fresh_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def state():
    """A ticket that clears every human_action condition."""
    return {
        "ticket": SupportTicket(
            ticket_id="T100",
            employee_id="E001",
            subject="VPN keeps dropping",
            description="Disconnects every few minutes.",
        ),
        "ticket_category": SupportCategory.vpn,
        "ticket_category_confidence": 0.92,
        "ticket_priority": SupportPriority.normal,
        "ticket_priority_confidence": 0.81,
        "graded_articles": [
            _graded("kb-vpn-003", ArticleRelevance.direct),
            _graded("kb-vpn-002", ArticleRelevance.partial),
            _graded("kb-vpn-005", ArticleRelevance.none),
        ],
        "triage_draft": TriageDraft(
            suggested_response="Hi Sarah, ...",
            cited_article_ids=["kb-vpn-003", "kb-vpn-002"],
        ),
    }


def _output(state):
    return build_triage_output_node(state)["triage_output"]


def test_confident_grounded_ticket_takes_action_lane(state):
    output = _output(state)

    assert output.ticket_id == "T100"
    assert output.needs_human_review is False
    assert output.category == SupportCategory.vpn
    assert output.category_confidence == 0.92
    assert output.priority == SupportPriority.normal
    assert output.priority_confidence == 0.81
    assert output.assigned_team == "Network Operations"
    assert output.assigned_team_confidence == 0.92
    assert output.suggested_response == "Hi Sarah, ..."
    assert output.knowledge_articles == ["kb-vpn-003", "kb-vpn-002"]


def test_low_category_confidence_needs_review(state):
    state["ticket_category_confidence"] = 0.79
    assert _output(state).needs_human_review is True


def test_low_priority_confidence_needs_review(state):
    state["ticket_priority_confidence"] = 0.69
    assert _output(state).needs_human_review is True


def test_critical_priority_always_needs_review(state):
    state["ticket_priority"] = SupportPriority.critical
    assert _output(state).needs_human_review is True


def test_reply_resting_only_on_partial_articles_needs_review(state):
    state["triage_draft"] = TriageDraft(
        suggested_response="Try this first ...", cited_article_ids=["kb-vpn-002"]
    )
    assert _output(state).needs_human_review is True


def test_uncited_direct_article_does_not_count(state):
    # A direct article exists, but the reply doesn't rely on it.
    state["triage_draft"] = TriageDraft(suggested_response="...", cited_article_ids=[])
    assert _output(state).needs_human_review is True


def test_invented_citation_is_dropped_and_forces_review(state):
    state["triage_draft"] = TriageDraft(
        suggested_response="...", cited_article_ids=["kb-vpn-003", "kb-vpn-099"]
    )

    output = _output(state)

    assert output.knowledge_articles == ["kb-vpn-003"]
    assert output.needs_human_review is True


def test_citation_of_article_graded_none_is_dropped(state):
    # The writer never saw "none" articles, so citing one is invalid.
    state["triage_draft"] = TriageDraft(
        suggested_response="...", cited_article_ids=["kb-vpn-003", "kb-vpn-005"]
    )

    output = _output(state)

    assert output.knowledge_articles == ["kb-vpn-003"]
    assert output.needs_human_review is True


def test_no_draft_means_no_response_and_review(state):
    del state["triage_draft"]

    output = _output(state)

    assert output.suggested_response is None
    assert output.knowledge_articles is None
    assert output.needs_human_review is True
    assert output.assigned_team == "Network Operations"


def test_debug_draft_placeholder_is_treated_as_no_draft(state):
    state["triage_draft"] = None

    output = _output(state)

    assert output.suggested_response is None
    assert output.needs_human_review is True


def test_thresholds_come_from_settings(state, monkeypatch):
    monkeypatch.setenv("L2_ACTION_MIN_CATEGORY_CONFIDENCE", "0.95")
    get_settings.cache_clear()

    assert _output(state).needs_human_review is True
