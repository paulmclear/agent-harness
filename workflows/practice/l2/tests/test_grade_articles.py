from types import SimpleNamespace

import pytest

from workflows.practice.l2.models import (
    ArticleRelevance,
    GradedArticle,
    KnowledgeBaseArticle,
    SupportTicket,
)
from workflows.practice.l2.nodes import grade_articles_node as node_module
from workflows.practice.l2.nodes.grade_articles_node import (
    RELEVANCE_CRITERIA,
    grade_articles_node,
)


class FakeClient:
    def __init__(self, answers: dict[str, tuple[str, float]]):
        self.answers = answers
        self.calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def system_one(self, state, questions):
        self.calls.append({"state": state, "questions": questions})
        return SimpleNamespace(
            choices={
                key: SimpleNamespace(choice=choice, confidence=confidence)
                for key, (choice, confidence) in self.answers.items()
            }
        )


def _article(article_id: str) -> KnowledgeBaseArticle:
    return KnowledgeBaseArticle(
        article_id=article_id, title="t", summary="s", content="c", tags=["vpn"]
    )


@pytest.fixture
def state():
    return {
        "ticket": SupportTicket(
            ticket_id="T100",
            employee_id="E001",
            subject="VPN keeps dropping",
            description="Disconnects every few minutes.",
        ),
        "kb_candidates": [_article("kb-vpn-003"), _article("kb-vpn-005")],
    }


@pytest.fixture
def install_client(monkeypatch):
    def install(answers: dict[str, tuple[str, float]]) -> FakeClient:
        client = FakeClient(answers)
        monkeypatch.setattr(node_module, "TypeSafeClient", lambda: client)
        return client

    return install


def test_criteria_cover_every_relevance_level():
    assert set(RELEVANCE_CRITERIA) == set(ArticleRelevance)


def test_grades_each_candidate_in_candidate_order(state, install_client):
    install_client(
        {
            "relevance_kb-vpn-003": ("direct", 0.91),
            "relevance_kb-vpn-005": ("none", 0.77),
        }
    )

    result = grade_articles_node(state)

    assert result == {
        "graded_articles": [
            GradedArticle(
                article_id="kb-vpn-003",
                relevance=ArticleRelevance.direct,
                confidence=0.91,
            ),
            GradedArticle(
                article_id="kb-vpn-005",
                relevance=ArticleRelevance.none,
                confidence=0.77,
            ),
        ]
    }


def test_asks_one_question_per_article_in_one_call(state, install_client):
    client = install_client(
        {
            "relevance_kb-vpn-003": ("direct", 0.9),
            "relevance_kb-vpn-005": ("partial", 0.6),
        }
    )

    grade_articles_node(state)

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["state"]["ticket"] == state["ticket"]
    assert set(call["state"]["articles"]) == {"kb-vpn-003", "kb-vpn-005"}
    assert set(call["questions"]) == {"relevance_kb-vpn-003", "relevance_kb-vpn-005"}
    for question in call["questions"].values():
        assert set(question.criteria) == {r.value for r in ArticleRelevance}


def test_no_candidates_skips_the_model_call(state, install_client):
    client = install_client({})
    state["kb_candidates"] = []

    assert grade_articles_node(state) == {"graded_articles": []}
    assert client.calls == []
