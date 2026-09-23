import pytest

from workflows.practice.l2.agents import _base
from workflows.practice.l2.agents._base import make_agent_node
from workflows.practice.l2.agents.triage_agent import (
    triage_agent_node,
    triage_prompt_inputs,
)
from workflows.practice.l2.models import (
    ArticleRelevance,
    Device,
    Employee,
    GradedArticle,
    KnowledgeBaseArticle,
    SupportCategory,
    SupportPriority,
    SupportTicket,
    TriageDraft,
)
from workflows.practice.l2.nodes.grade_articles_node import route_after_grading


def _article(article_id: str) -> KnowledgeBaseArticle:
    return KnowledgeBaseArticle(
        article_id=article_id,
        title=f"Title {article_id}",
        summary=f"Summary {article_id}",
        content=f"Content {article_id}",
        tags=["vpn"],
    )


def _graded(article_id: str, relevance: ArticleRelevance) -> GradedArticle:
    return GradedArticle(article_id=article_id, relevance=relevance, confidence=0.9)


@pytest.fixture
def state():
    return {
        "debug": False,
        "ticket": SupportTicket(
            ticket_id="T100",
            employee_id="E001",
            subject="VPN keeps dropping",
            description="Disconnects every few minutes.",
        ),
        "employee": Employee(
            employee_id="E001",
            name="Sarah Jones",
            department="Finance",
            office="London",
            email="sarah.jones@company.com",
            device_ids=["LT-2841"],
        ),
        "devices": [
            Device(
                device_id="LT-2841",
                os="Windows 11",
                managed=True,
                last_seen="2026-09-22",
            )
        ],
        "ticket_category": SupportCategory.vpn,
        "ticket_priority": SupportPriority.normal,
        "kb_candidates": [
            _article("kb-vpn-003"),
            _article("kb-vpn-005"),
            _article("kb-vpn-002"),
        ],
        "graded_articles": [
            _graded("kb-vpn-003", ArticleRelevance.direct),
            _graded("kb-vpn-005", ArticleRelevance.none),
            _graded("kb-vpn-002", ArticleRelevance.partial),
        ],
    }


# --- routing -----------------------------------------------------------------


def test_direct_article_goes_straight_to_triage_agent(state):
    assert route_after_grading(state) == "triage_agent"


@pytest.mark.parametrize(
    "graded",
    [
        [],
        [_graded("kb-vpn-005", ArticleRelevance.none)],
        [_graded("kb-vpn-002", ArticleRelevance.partial)],
    ],
    ids=["nothing", "none-only", "partial-only"],
)
def test_no_direct_article_escalates_once(state, graded):
    state["graded_articles"] = graded
    assert route_after_grading(state) == "kb_search_agent"


def test_after_escalation_partial_articles_still_get_a_draft(state):
    state["kb_escalated"] = True
    state["graded_articles"] = [_graded("kb-vpn-002", ArticleRelevance.partial)]
    assert route_after_grading(state) == "triage_agent"


def test_after_escalation_nothing_usable_skips_the_draft(state):
    state["kb_escalated"] = True
    state["graded_articles"] = [_graded("kb-vpn-005", ArticleRelevance.none)]
    assert route_after_grading(state) == "build_triage_output"


# --- prompt inputs -----------------------------------------------------------


def test_prompt_includes_only_direct_and_partial_articles(state):
    articles = triage_prompt_inputs(state)["articles"]

    assert "kb-vpn-003" in articles
    assert "kb-vpn-002" in articles
    assert "kb-vpn-005" not in articles


def test_prompt_articles_carry_relevance_and_full_content(state):
    articles = triage_prompt_inputs(state)["articles"]

    assert "[kb-vpn-003] (direct)" in articles
    assert "[kb-vpn-002] (partial)" in articles
    assert "Content kb-vpn-003" in articles


def test_prompt_includes_employee_and_classification(state):
    inputs = triage_prompt_inputs(state)

    assert inputs["employee_name"] == "Sarah Jones"
    assert inputs["category"] == "vpn"
    assert inputs["priority"] == "normal"
    assert "LT-2841 (Windows 11, managed)" in inputs["devices"]


# --- node behaviour ----------------------------------------------------------


def test_debug_mode_skips_the_model(state):
    state["debug"] = True
    assert triage_agent_node(state) == {"triage_draft": None}


class FakeAgent:
    def __init__(self, structured_response):
        self.structured_response = structured_response
        self.prompts: list[str] = []

    def invoke(self, payload):
        self.prompts.append(payload["messages"][0].content)
        return {"messages": [], "structured_response": self.structured_response}


def test_structured_agent_writes_structured_response_to_state(state, monkeypatch):
    draft = TriageDraft(
        suggested_response="Hi Sarah, ...", cited_article_ids=["kb-vpn-003"]
    )
    fake = FakeAgent(draft)
    captured: dict = {}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return fake

    monkeypatch.setattr(_base, "create_agent", fake_create_agent)
    node = make_agent_node(
        name="test_structured",
        system_prompt="sys",
        user_prompt_template="Ticket {ticket_id}: {articles}",
        output_state_key="triage_draft",
        response_format=TriageDraft,
        prompt_inputs=lambda s: {"ticket_id": s["ticket"].ticket_id, "articles": "A"},
    )

    assert node(state) == {"triage_draft": draft}
    assert captured["response_format"] is TriageDraft
    assert fake.prompts == ["Ticket T100: A"]
