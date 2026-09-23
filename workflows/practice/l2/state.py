from typing import TypedDict

from workflows.practice.l2.models import SecurityAssessment, SupportCategory, SupportTicket, TriageOutput, Employee, Device, KnowledgeBaseArticle, GradedArticle, TriageDraft


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
    ticket_priority: str
    ticket_priority_confidence: float

    kb_candidates: list[KnowledgeBaseArticle]
    graded_articles: list[GradedArticle]
    triage_draft: TriageDraft | None

    # output data
    triage_output: TriageOutput
