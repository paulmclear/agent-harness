import logging

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.models import SupportCategory, SupportTicket
from workflows.practice.l2.state import State
from workflows.practice.l2.tools.knowledge_base import search_kb

logger = logging.getLogger(__name__)


def build_kb_query(ticket: SupportTicket, category: SupportCategory) -> str:
    """Compose the first-pass KB query from the ticket text plus its category.

    The category term matches article tags (weighted highest by ``search_kb``),
    so it nudges same-category articles up without filtering others out.
    """
    return " ".join(
        part for part in (ticket.subject, ticket.description, category.value) if part
    )


def kb_lookup_node(state: State) -> dict:
    """Deterministic first-pass KB search; always runs on the ordinary path (see ADR-001)."""

    query = build_kb_query(state["ticket"], state["ticket_category"])
    candidates = search_kb(query, limit=get_settings().kb_lookup_limit)

    logger.info(
        "KB lookup returned %d candidate(s): %s",
        len(candidates),
        [a.article_id for a in candidates],
    )

    return {"kb_candidates": candidates}
