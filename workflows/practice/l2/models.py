from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class SupportTicket(BaseModel):
    ticket_id: str
    employee_id: str
    subject: str
    description: str


class SecurityReason(Enum):
    phishing = "phishing"
    malware = "malware"
    lost_stolen_device = "lost_stolen_device"
    compromised_account = "compromised_account"
    data_exposure = "data_exposure"
    vulnerability = "vulnerability"
    other = "other"


class SecurityAssessment(BaseModel):
    security_related: bool = Field(default=False)
    security_probability: float = Field(default=0)
    reason: SecurityReason | None = Field(default=None)
    reason_confidence: float = Field(default=0)


class Employee(BaseModel):
    employee_id: str
    name: str
    department: str
    office: str
    email: str
    device_ids: list[str] = Field(default_factory=list)


class Device(BaseModel):
    device_id: str
    os: str
    managed: bool
    last_seen: str


class KnowledgeBaseArticle(BaseModel):
    article_id: str
    title: str
    summary: str
    content: str
    tags: list[str]


class SupportCategory(Enum):
    security = "security"
    vpn = "vpn"
    email = "email"
    hardware = "hardware"
    software = "software"
    identity = "identity"
    network = "network"
    other = "other"


class SupportPriority(Enum):
    critical = "critical"
    high = "high"
    normal = "normal"
    low = "low"


class TriageOutput(BaseModel):
    ticket_id: str

    needs_human_review: bool

    category: SupportCategory
    category_confidence: float

    priority: SupportPriority
    priority_confidence: float

    assigned_team: str
    assigned_team_confidence: float

    suggested_response: Optional[str] = None
    knowledge_articles: Optional[list[str]] = None


class ArticleRelevance(Enum):
    direct = "direct"
    partial = "partial"
    none = "none"


class GradedArticle(BaseModel):
    """A KB candidate with its relevance to the ticket, as judged by grade_articles."""

    article_id: str
    relevance: ArticleRelevance
    confidence: float


class TriageDraft(BaseModel):
    """What triage_agent writes; build_triage_output validates and assembles the rest."""

    suggested_response: str = Field(
        description="Reply to the employee, grounded only in the provided KB articles."
    )
    cited_article_ids: list[str] = Field(
        description="IDs of the KB articles the reply actually relies on."
    )
