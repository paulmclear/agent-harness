import os

import pytest

from workflows.practice.l1.nodes.build_report_node import build_report_node
from workflows.practice.l1.tools import (
    Customer,
    PolicyChunk,
    RiskAssessment,
    RiskFactor,
)


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="graph run calls the LLM")
def test_graph_end_to_end_produces_explained_report(tmp_path, monkeypatch):
    from workflows.practice.l1.graph import build_graph

    monkeypatch.chdir(tmp_path)
    final = build_graph().invoke({"customer_id": "C-30355"})

    assert final["risk"].rating == "high"
    assert final["policy_chunks"], "policy search node should populate matches"
    assert (tmp_path / "report_C-30355.md").read_text() == final["report"]


@pytest.fixture
def report_state() -> dict:
    return {
        "customer_id": "C-1",
        "customer": Customer(
            customer_id="C-1", name="Test", country="NG", industry="Retail",
            annual_turnover=1, years_in_business=1,
        ),
        "risk": RiskAssessment(
            score=2,
            factors=[RiskFactor(code="HIGH_RISK_COUNTRY", description="Located in NG.", points=2)],
        ),
        "policy_chunks": [
            PolicyChunk(id="POL-14", title="High-risk jurisdictions", text="EDD required.", score=1.0)
        ],
        "risk_assessment_output": "## Summary\nAGENT TEXT",
    }


def test_build_report_lists_facts(report_state):
    report = build_report_node(report_state)["report"]
    assert "MEDIUM" in report
    assert "HIGH_RISK_COUNTRY" in report
    assert "Located in NG." in report
    assert "POL-14" in report


def test_build_report_puts_facts_before_assessment(report_state):
    report = build_report_node(report_state)["report"]
    facts = report.index("Part 1")
    assessment = report.index("Part 2")
    assert facts < report.index("POL-14") < assessment < report.index("AGENT TEXT")
    assert report.rstrip().endswith("AGENT TEXT")
