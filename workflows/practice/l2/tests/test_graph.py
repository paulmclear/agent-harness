from types import SimpleNamespace

import pytest

from workflows.practice.l2.graph import build_graph
from workflows.practice.l2.models import (
    SupportCategory,
    SupportPriority,
    SupportTicket,
)
from workflows.practice.l2.nodes import (
    classify_security_risk_node,
    classify_ticket_node,
    grade_articles_node,
)


class FakeTypeSafeClient:
    """Stands in for ``TypeSafeClient`` in every node that calls it.

    Choice questions not listed in ``choices`` (e.g. per-article relevance
    questions) are answered with ``default_choice``.
    """

    def __init__(
        self,
        nouls: dict[str, float],
        choices: dict[str, tuple[str, float]],
        default_choice: tuple[str, float],
    ):
        self.nouls = nouls
        self.choices = choices
        self.default_choice = default_choice

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def system_one(self, state, questions):
        return SimpleNamespace(
            nouls={
                key: SimpleNamespace(noul=value) for key, value in self.nouls.items()
            },
            choices={
                key: SimpleNamespace(choice=choice, confidence=confidence)
                for key in questions
                for choice, confidence in [self.choices.get(key, self.default_choice)]
            },
        )


@pytest.fixture
def fake_typesafe(monkeypatch):
    """Install a fake TypeSafe client with the given answers; returns an installer."""

    def install(security_probability: float, relevance: str = "direct") -> None:
        client = FakeTypeSafeClient(
            nouls={"has_security_implications": security_probability},
            choices={
                "security_reason_classification": ("lost_stolen_device", 0.9),
                "ticket_category": ("vpn", 0.92),
                "ticket_priority": ("high", 0.81),
            },
            default_choice=(relevance, 0.9),
        )
        for module in (
            classify_security_risk_node,
            classify_ticket_node,
            grade_articles_node,
        ):
            monkeypatch.setattr(module, "TypeSafeClient", lambda: client)

    return install


@pytest.fixture
def ticket():
    return SupportTicket(
        ticket_id="T001",
        employee_id="E001",
        subject="VPN keeps dropping",
        description="Disconnects every few minutes.",
    )


def test_graph_compiles():
    graph = build_graph()
    assert {
        "populate_ticket_details",
        "classify_security_risk",
        "classify_ticket",
        "kb_lookup",
        "grade_articles",
        "security_handoff",
        "kb_search_agent",
        "triage_agent",
        "build_triage_output",
    } <= set(graph.nodes)


def test_security_ticket_takes_handoff_path(fake_typesafe, ticket):
    fake_typesafe(security_probability=0.9)

    result = build_graph().invoke({"ticket": ticket, "debug": True})

    output = result["triage_output"]
    assert output.ticket_id == "T001"
    assert output.assigned_team == "Cyber Security Operations"
    assert output.needs_human_review is True
    assert "ticket_category" not in result
    assert "kb_candidates" not in result


def test_ordinary_ticket_takes_triage_path(fake_typesafe, ticket):
    fake_typesafe(security_probability=0.1)

    result = build_graph().invoke({"ticket": ticket, "debug": True})

    assert result["security_assessment"].security_related is False
    assert result["ticket_category"] == SupportCategory.vpn
    assert result["ticket_priority"] == SupportPriority.high
    # kb_lookup always runs; every candidate it finds gets graded
    candidate_ids = [a.article_id for a in result["kb_candidates"]]
    assert candidate_ids
    assert [g.article_id for g in result["graded_articles"]] == candidate_ids
    # a direct article routes straight to triage_agent (no escalation), which
    # skips the model in debug mode
    assert "kb_escalated" not in result
    assert result["triage_draft"] is None
    # both paths converge on TriageOutput
    output = result["triage_output"]
    assert output.ticket_id == "T001"
    assert output.assigned_team == "Network Operations"
    # no draft in debug mode, so no grounded reply: review lane
    assert output.suggested_response is None
    assert output.needs_human_review is True


def test_no_direct_article_escalates_once_then_builds_output(fake_typesafe, ticket):
    fake_typesafe(security_probability=0.1, relevance="none")

    result = build_graph().invoke({"ticket": ticket, "debug": True})

    # escalated once; nothing usable came back, so no draft was attempted
    assert result["kb_escalated"] is True
    assert result["kb_candidates"] == []
    assert "triage_draft" not in result
    output = result["triage_output"]
    assert output.suggested_response is None
    assert output.knowledge_articles is None
    assert output.needs_human_review is True
