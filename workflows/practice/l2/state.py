from typing import TypedDict

from workflows.practice.l2.models import (
    Device,
    Employee,
    GradedArticle,
    KnowledgeBaseArticle,
    SecurityAssessment,
    SupportCategory,
    SupportPriority,
    SupportTicket,
    TriageDraft,
    TriageOutput,
)


class InputState(TypedDict):
    """Keys accepted by ``graph.invoke``. Everything else is derived by nodes."""

    # control
    debug: bool

    # input data
    ticket: SupportTicket


class State(InputState):
    
    # intermediate derived data
    employee: Employee
    devices: list[Device]

    security_assessment: SecurityAssessment
    ticket_category: SupportCategory
    ticket_category_confidence: float
    ticket_priority: SupportPriority
    ticket_priority_confidence: float

    kb_candidates: list[KnowledgeBaseArticle]
    graded_articles: list[GradedArticle]
    kb_escalated: bool  # set by kb_search_agent; allows one escalation per ticket
    triage_draft: TriageDraft | None

    # output data
    triage_output: TriageOutput
