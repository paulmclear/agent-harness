import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()

_PERPLEXITY_BASE_URL = "https://api.perplexity.ai"


def _build_llm(model: str) -> ChatOpenAI:
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    return ChatOpenAI(
        model=model,
        api_key=SecretStr(api_key) if api_key else None,
        base_url=_PERPLEXITY_BASE_URL,
    )


@tool
def perplexity_search(
    query: str,
    model: Literal[
        "sonar", "sonar-pro", "sonar-reasoning", "sonar-reasoning-pro"
    ] = "sonar",
    search_recency_filter: Literal["hour", "day", "week", "month", "year"] | None = None,
) -> dict:
    """Search the web with Perplexity and return a grounded answer with citations.

    Args:
        query: The natural-language question to answer.
        model: Perplexity Sonar model to use. `sonar` is fast/cheap; `sonar-pro`
            does deeper search; `sonar-reasoning*` adds chain-of-thought.
        search_recency_filter: Optional time window to restrict sources.

    Returns:
        Dict with `answer` (str) and `citations` (list[str]).
    """
    llm = _build_llm(model)
    if search_recency_filter is not None:
        llm = llm.bind(extra_body={"search_recency_filter": search_recency_filter})

    response = llm.invoke([HumanMessage(content=query)])

    answer = response.content if isinstance(response.content, str) else str(response.content)
    citations = (
        response.response_metadata.get("citations")
        or response.additional_kwargs.get("citations")
        or []
    )

    return {"answer": answer, "citations": list(citations)}
