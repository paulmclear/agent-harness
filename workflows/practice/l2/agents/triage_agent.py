"""Tool-free writer that drafts the employee reply from graded KB articles.

It only runs when grading found at least one ``direct`` or ``partial``
article (see ``route_after_grading`` and ADR-001). It drafts the reply and
names the articles it relied on; ``build_triage_output`` validates those IDs
and assembles the final ``TriageOutput``.
"""

import textwrap

from workflows.practice.l2.agents._base import make_agent_node
from workflows.practice.l2.models import ArticleRelevance, TriageDraft
from workflows.practice.l2.state import State

USABLE_RELEVANCE = frozenset({ArticleRelevance.direct, ArticleRelevance.partial})

SYSTEM_PROMPT = textwrap.dedent("""
    You are an IT service desk analyst drafting a reply to an employee's
    support ticket. A colleague on the service desk will review your draft and
    may send it as written, so write it ready to send.

    Ground rules:
    - Use only the knowledge-base articles provided. Do not add steps, links,
      settings, or policies that are not in them.
    - Articles marked "direct" address the issue; build the reply on them.
      Articles marked "partial" are related background; use them only for
      first steps or context, and say that the service desk will follow up if
      those steps do not resolve it.
    - If the articles do not actually help with this ticket, say so briefly
      and tell the employee the service desk will be in touch. Do not guess.
    - Never ask for a password, MFA code, or other secret.
    - Do not promise actions, timelines, or outcomes the articles do not
      support.

    Style: address the employee by first name, plain language, short numbered
    steps where there are steps, no more than about 150 words.

    In cited_article_ids, list only the IDs of articles your reply actually
    relies on, exactly as given.
""").strip()

USER_PROMPT_TEMPLATE = textwrap.dedent("""
    Date: {current_date}

    Ticket {ticket_id}
    Subject: {subject}
    Description: {description}

    Employee: {employee_name} ({department}, {office})
    Devices: {devices}

    Category: {category}
    Priority: {priority}

    Knowledge-base articles:
    {articles}
""").strip()


def _format_articles(state: State) -> str:
    relevance_by_id = {
        g.article_id: g.relevance
        for g in state["graded_articles"]
        if g.relevance in USABLE_RELEVANCE
    }
    blocks = [
        f"[{a.article_id}] ({relevance_by_id[a.article_id].value}) {a.title}\n"
        f"Summary: {a.summary}\n"
        f"{a.content}"
        for a in state["kb_candidates"]
        if a.article_id in relevance_by_id
    ]
    return "\n\n".join(blocks)


def triage_prompt_inputs(state: State) -> dict:
    """Template values for the triage prompt, including only usable articles."""
    ticket = state["ticket"]
    employee = state["employee"]
    devices = ", ".join(
        f"{d.device_id} ({d.os}, {'managed' if d.managed else 'unmanaged'})"
        for d in state["devices"]
    )
    return {
        "ticket_id": ticket.ticket_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "employee_name": employee.name,
        "department": employee.department,
        "office": employee.office,
        "devices": devices or "none on record",
        "category": state["ticket_category"].value,
        "priority": state["ticket_priority"].value,
        "articles": _format_articles(state),
    }


triage_agent_node = make_agent_node(
    name="triage_agent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt_template=USER_PROMPT_TEMPLATE,
    output_state_key="triage_draft",
    response_format=TriageDraft,
    prompt_inputs=triage_prompt_inputs,
)
