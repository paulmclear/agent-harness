import logging

from typesafe_sdk import Choice, TypeSafeClient

from workflows.practice.l2.models import ArticleRelevance, GradedArticle
from workflows.practice.l2.state import State

logger = logging.getLogger(__name__)


RELEVANCE_CRITERIA: dict[ArticleRelevance, str] = {
    ArticleRelevance.direct: (
        "The article addresses the employee's actual issue: following it would "
        "resolve the problem or answer the question in `ticket`."
    ),
    ArticleRelevance.partial: (
        "The article covers the same system or a closely related problem and "
        "gives useful background or first steps, but does not resolve the issue."
    ),
    ArticleRelevance.none: (
        "The article shares keywords with the ticket but is about a different "
        "problem, or would not help the employee."
    ),
}


def _question_key(article_id: str) -> str:
    return f"relevance_{article_id}"


def grade_articles_node(state: State) -> dict:
    """Grade every KB candidate's relevance to the ticket in one TypeSafe call.

    This is the single judge of relevance (ADR-001): first-pass lookup results
    and kb_search_agent picks are both graded here.
    """

    candidates = state["kb_candidates"]
    if not candidates:
        return {"graded_articles": []}

    questions = {
        _question_key(article.article_id): Choice(
            instructions=(
                f"How relevant is the knowledge-base article "
                f"`articles.{article.article_id}` to the issue the employee "
                f"raises in `ticket`?"
            ),
            criteria={
                relevance.value: description
                for relevance, description in RELEVANCE_CRITERIA.items()
            },
        )
        for article in candidates
    }
    inputs = {
        "ticket": state["ticket"],
        "articles": {article.article_id: article for article in candidates},
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=inputs, questions=questions)

    graded = []
    for article in candidates:
        answer = response.choices[_question_key(article.article_id)]
        graded.append(
            GradedArticle(
                article_id=article.article_id,
                relevance=ArticleRelevance(answer.choice),
                confidence=answer.confidence,
            )
        )

    logger.info(
        "Graded articles: %s",
        [(g.article_id, g.relevance.value, round(g.confidence, 2)) for g in graded],
    )

    return {"graded_articles": graded}


def route_after_grading(state: State) -> str:
    """Pick the next step from the grades (ADR-001).

    - any ``direct`` article: draft the reply
    - otherwise, escalate to ``kb_search_agent`` once
    - after escalating: draft from ``partial`` articles if any, else build the
      output with no suggested reply
    """
    relevances = {g.relevance for g in state["graded_articles"]}
    if ArticleRelevance.direct in relevances:
        return "triage_agent"
    if not state.get("kb_escalated"):
        return "kb_search_agent"
    if ArticleRelevance.partial in relevances:
        return "triage_agent"
    return "build_triage_output"
