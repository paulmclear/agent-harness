import pytest
from langchain_core.messages import AIMessage, ToolMessage

from workflows.practice.l2.agents.kb_search_agent import (
    KbSearchResult,
    collect_picked_articles,
    kb_search_agent_node,
    kb_search_prompt_inputs,
    search_knowledge_base,
)
from workflows.practice.l2.models import (
    ArticleRelevance,
    GradedArticle,
    KnowledgeBaseArticle,
    SupportCategory,
    SupportTicket,
)


def _article(article_id: str) -> KnowledgeBaseArticle:
    return KnowledgeBaseArticle(
        article_id=article_id,
        title=f"Title {article_id}",
        summary=f"Summary {article_id}",
        content=f"Content {article_id}",
        tags=[],
    )


def _tool_message(articles: list[KnowledgeBaseArticle]) -> ToolMessage:
    return ToolMessage(content="...", tool_call_id="call", artifact=articles)


@pytest.fixture
def state():
    return {
        "debug": True,
        "ticket": SupportTicket(
            ticket_id="T100",
            employee_id="E001",
            subject="Can't get in",
            description="Locked out after the weekend.",
        ),
        "ticket_category": SupportCategory.identity,
        "kb_candidates": [_article("kb-a"), _article("kb-b")],
        "graded_articles": [
            GradedArticle(
                article_id="kb-a", relevance=ArticleRelevance.partial, confidence=0.7
            ),
            GradedArticle(
                article_id="kb-b", relevance=ArticleRelevance.none, confidence=0.8
            ),
        ],
    }


# --- tool --------------------------------------------------------------------


def test_tool_returns_summary_text_and_articles_as_artifact():
    text, articles = search_knowledge_base.func("vpn disconnects")

    assert articles
    assert all(isinstance(a, KnowledgeBaseArticle) for a in articles)
    assert f"[{articles[0].article_id}]" in text


def test_tool_reports_no_matches():
    text, articles = search_knowledge_base.func("zzzqqq")

    assert articles == []
    assert text == "No articles found."


# --- response parsing --------------------------------------------------------


def test_collects_picked_articles_that_a_search_returned():
    response = {
        "messages": [
            _tool_message([_article("kb-1"), _article("kb-2")]),
            _tool_message([_article("kb-2"), _article("kb-3")]),
            AIMessage(content="done"),
        ],
        "structured_response": KbSearchResult(article_ids=["kb-3", "kb-1"]),
    }

    assert [a.article_id for a in collect_picked_articles(response)] == ["kb-3", "kb-1"]


def test_drops_picks_no_search_returned():
    response = {
        "messages": [_tool_message([_article("kb-1")])],
        "structured_response": KbSearchResult(article_ids=["kb-1", "kb-invented"]),
    }

    assert [a.article_id for a in collect_picked_articles(response)] == ["kb-1"]


def test_missing_structured_response_yields_no_picks():
    response = {"messages": [_tool_message([_article("kb-1")])]}

    assert collect_picked_articles(response) == []


# --- prompt ------------------------------------------------------------------


def test_prompt_shows_first_query_and_what_it_found(state):
    inputs = kb_search_prompt_inputs(state)

    assert (
        inputs["first_query"] == "Can't get in Locked out after the weekend. identity"
    )
    assert "[kb-a] Title kb-a (partial)" in inputs["already_found"]
    assert "[kb-b] Title kb-b (none)" in inputs["already_found"]
    assert inputs["category"] == "identity"


# --- node --------------------------------------------------------------------


def test_node_keeps_usable_first_pass_articles_and_marks_escalated(state):
    # debug mode: the agent is skipped, so it contributes no picks
    result = kb_search_agent_node(state)

    assert [a.article_id for a in result["kb_candidates"]] == ["kb-a"]
    assert result["kb_escalated"] is True
