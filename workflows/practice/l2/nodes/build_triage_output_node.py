"""Assemble the ordinary-path ``TriageOutput`` deterministically.

The LLM steps upstream propose (category, priority, relevance, draft reply);
this node checks and decides: it validates the draft's citations, looks up the
support team, and picks the lane (``human_action`` vs ``human_review``).
"""

import logging

from workflows.practice.l2.config import Settings, get_settings
from workflows.practice.l2.models import (
    ArticleRelevance,
    GradedArticle,
    SupportPriority,
    TriageOutput,
)
from workflows.practice.l2.state import State
from workflows.practice.l2.tools.it_service_catalogue import get_support_team

logger = logging.getLogger(__name__)

# The writer only sees these, so only these can be cited.
CITABLE_RELEVANCE = frozenset({ArticleRelevance.direct, ArticleRelevance.partial})


def review_reasons(
    *,
    category_confidence: float,
    priority: SupportPriority,
    priority_confidence: float,
    graded: list[GradedArticle],
    cited_ids: list[str],
    dropped_ids: list[str],
    has_draft: bool,
    settings: Settings,
) -> list[str]:
    """Return why a ticket needs human review; empty means ``human_action``."""
    reasons = []
    if category_confidence < settings.action_min_category_confidence:
        reasons.append(f"category confidence {category_confidence:.2f}")
    if priority_confidence < settings.action_min_priority_confidence:
        reasons.append(f"priority confidence {priority_confidence:.2f}")
    if priority in settings.review_always_priorities:
        reasons.append(f"priority {priority.value} always reviewed")
    if not has_draft:
        reasons.append("no grounded reply")
    if dropped_ids:
        reasons.append(f"invalid citations {dropped_ids}")

    direct_ids = {
        g.article_id for g in graded if g.relevance == ArticleRelevance.direct
    }
    cited_direct = sum(1 for article_id in cited_ids if article_id in direct_ids)
    if has_draft and cited_direct < settings.action_min_direct_articles:
        reasons.append(f"reply cites {cited_direct} direct article(s)")
    return reasons


def build_triage_output_node(state: State) -> dict:
    """Build the final ``TriageOutput`` for a non-security ticket."""
    settings = get_settings()
    graded = state.get("graded_articles", [])
    draft = state.get("triage_draft")

    citable = {g.article_id for g in graded if g.relevance in CITABLE_RELEVANCE}
    cited_ids = [i for i in draft.cited_article_ids if i in citable] if draft else []
    dropped_ids = (
        [i for i in draft.cited_article_ids if i not in citable] if draft else []
    )

    category = state["ticket_category"]
    category_confidence = state["ticket_category_confidence"]
    priority = state["ticket_priority"]
    priority_confidence = state["ticket_priority_confidence"]

    reasons = review_reasons(
        category_confidence=category_confidence,
        priority=priority,
        priority_confidence=priority_confidence,
        graded=graded,
        cited_ids=cited_ids,
        dropped_ids=dropped_ids,
        has_draft=draft is not None,
        settings=settings,
    )
    if dropped_ids:
        logger.warning("Dropped citations not in graded set: %s", dropped_ids)
    logger.info(
        "Lane: %s%s",
        "human_review" if reasons else "human_action",
        f" ({'; '.join(reasons)})" if reasons else "",
    )

    triage_output = TriageOutput(
        ticket_id=state["ticket"].ticket_id,
        needs_human_review=bool(reasons),
        category=category,
        category_confidence=category_confidence,
        priority=priority,
        priority_confidence=priority_confidence,
        assigned_team=get_support_team(category.value, security_related=False),
        # the team is a fixed lookup from category, so it is as certain as the category
        assigned_team_confidence=category_confidence,
        suggested_response=draft.suggested_response if draft else None,
        knowledge_articles=cited_ids if draft else None,
    )
    return {"triage_output": triage_output}
