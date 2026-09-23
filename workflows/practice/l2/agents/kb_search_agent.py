"""Fallback KB search agent, used when the first-pass lookup finds nothing ``direct``.

The agent rewrites queries and calls ``search_kb`` (at most
``kb_agent_max_tool_calls`` times, enforced by middleware) and returns the IDs
it thinks fit. Its picks are only candidates: they go back through
``grade_articles``, the single relevance judge (ADR-001). Picks that no search
actually returned are dropped here.
"""

import textwrap

from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from workflows.practice.l2.agents._base import make_agent_node
from workflows.practice.l2.config import get_settings
from workflows.practice.l2.models import ArticleRelevance, KnowledgeBaseArticle
from workflows.practice.l2.nodes.kb_lookup_node import build_kb_query
from workflows.practice.l2.state import State
from workflows.practice.l2.tools.knowledge_base import search_kb

USABLE_RELEVANCE = frozenset({ArticleRelevance.direct, ArticleRelevance.partial})


class KbSearchResult(BaseModel):
    article_ids: list[str] = Field(
        description=(
            "IDs of articles, from your search results, that address the "
            "employee's issue. Empty if none do."
        )
    )


@tool(response_format="content_and_artifact")
def search_knowledge_base(query: str) -> tuple[str, list[KnowledgeBaseArticle]]:
    """Search the IT knowledge base. Matches keywords, so try the words an
    article title would use (e.g. "password reset", "account locked")."""
    articles = search_kb(query, limit=get_settings().kb_lookup_limit)
    if not articles:
        return "No articles found.", []
    text = "\n".join(f"[{a.article_id}] {a.title}: {a.summary}" for a in articles)
    return text, articles


SYSTEM_PROMPT = textwrap.dedent("""
    You find knowledge-base articles for IT support tickets. A first keyword
    search has already run and found nothing that directly addresses the
    ticket. Your job is to search again with better queries.

    The search matches keywords, not meaning. Rewrite the employee's wording
    into the terms an article would use: the system involved, the symptom, and
    the likely fix (e.g. "can't get in" -> "account locked", "password reset").
    Do not repeat the first query.

    You have a small search budget. Stop as soon as you find an article that
    directly addresses the issue. Return only IDs that appeared in your search
    results, and only for articles that would help; return an empty list if
    none do. The category is a hint and may be wrong.
""").strip()

USER_PROMPT_TEMPLATE = textwrap.dedent("""
    Subject: {subject}
    Description: {description}
    Category (hint): {category}

    First query: {first_query}
    It found:
    {already_found}
""").strip()


def kb_search_prompt_inputs(state: State) -> dict:
    """Template values: the ticket plus what the first-pass search already tried."""
    ticket = state["ticket"]
    relevance_by_id = {g.article_id: g.relevance for g in state["graded_articles"]}
    already_found = "\n".join(
        f"- [{a.article_id}] {a.title} ({relevance_by_id[a.article_id].value})"
        for a in state["kb_candidates"]
        if a.article_id in relevance_by_id
    )
    return {
        "subject": ticket.subject,
        "description": ticket.description,
        "category": state["ticket_category"].value,
        "first_query": build_kb_query(ticket, state["ticket_category"]),
        "already_found": already_found or "- nothing",
    }


def collect_picked_articles(response: dict) -> list[KnowledgeBaseArticle]:
    """Return the agent's picks, keeping only articles its searches returned."""
    seen: dict[str, KnowledgeBaseArticle] = {}
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and message.artifact:
            for article in message.artifact:
                seen.setdefault(article.article_id, article)

    result = response.get("structured_response")
    picked_ids = dict.fromkeys(result.article_ids) if result else {}
    return [seen[article_id] for article_id in picked_ids if article_id in seen]


_search_agent = make_agent_node(
    name="kb_search_agent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt_template=USER_PROMPT_TEMPLATE,
    output_state_key="picks",
    tools=[search_knowledge_base],
    response_format=KbSearchResult,
    prompt_inputs=kb_search_prompt_inputs,
    middleware=lambda: [
        # "continue" blocks further searches but lets the agent still answer
        ToolCallLimitMiddleware(
            tool_name=search_knowledge_base.name,
            run_limit=get_settings().kb_agent_max_tool_calls,
            exit_behavior="continue",
        )
    ],
    parse_response=collect_picked_articles,
)


def kb_search_agent_node(state: State) -> dict:
    """Run the fallback search and set up the candidates for regrading.

    Usable first-pass articles (``partial``) are kept alongside the agent's
    picks, so a weak-but-useful first result isn't lost. Everything is
    regraded by ``grade_articles``.
    """
    picks = _search_agent(state)["picks"] or []

    usable_ids = {
        g.article_id
        for g in state["graded_articles"]
        if g.relevance in USABLE_RELEVANCE
    }
    kept = [a for a in state["kb_candidates"] if a.article_id in usable_ids]
    merged = {a.article_id: a for a in [*kept, *picks]}

    return {"kb_candidates": list(merged.values()), "kb_escalated": True}
