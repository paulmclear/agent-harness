from types import SimpleNamespace

import pytest

from workflows.practice.l2.models import SupportCategory, SupportPriority
from workflows.practice.l2.nodes import classify_ticket_node as node_module
from workflows.practice.l2.nodes.classify_ticket_node import (
    CATEGORY_CRITERIA,
    PRIORITY_CRITERIA,
    classify_ticket_node,
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


@pytest.fixture
def fake_client(monkeypatch):
    client = FakeClient(
        {"ticket_category": ("vpn", 0.92), "ticket_priority": ("normal", 0.81)}
    )
    monkeypatch.setattr(node_module, "TypeSafeClient", lambda: client)
    return client


# `security` is assigned only by security_handoff, never by the ordinary-path classifier.
ORDINARY_CATEGORIES = set(SupportCategory) - {SupportCategory.security}


def test_criteria_cover_every_ordinary_category():
    assert set(CATEGORY_CRITERIA) == ORDINARY_CATEGORIES


def test_returns_category_and_priority_with_confidence(fake_client):
    result = classify_ticket_node({"ticket": "VPN keeps dropping"})

    assert result == {
        "ticket_category": SupportCategory.vpn,
        "ticket_category_confidence": 0.92,
        "ticket_priority": SupportPriority.normal,
        "ticket_priority_confidence": 0.81,
    }


def test_asks_both_questions_in_one_call(fake_client):
    classify_ticket_node({"ticket": "VPN keeps dropping"})

    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["state"] == {"ticket": "VPN keeps dropping"}
    questions = call["questions"]
    assert set(questions["ticket_category"].criteria) == {
        c.value for c in ORDINARY_CATEGORIES
    }
    assert set(questions["ticket_priority"].criteria) == {
        p.value for p in PRIORITY_CRITERIA
    }
