"""Shared Perplexity sonar-pro chat helper for Layer-1 collector fetchers.

Mirrors `n8n-nodes-base.perplexity` with `simplify` unset — returns
`choices[0].message.content` as plain text — and applies the spec's
`search_recency: month` window.
"""

from __future__ import annotations

import datetime as dt

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_perplexity import ChatPerplexity

load_dotenv()

_RESEARCHER_SYSTEM_PROMPT = (
    "You are a financial crime compliance researcher. Today's date is {today}. "
    "Return ONLY factual information from verifiable sources with citations."
)


def today() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def researcher_system_prompt() -> str:
    return _RESEARCHER_SYSTEM_PROMPT.format(today=today())


def perplexity_chat(system_prompt: str, user_prompt: str) -> str:
    llm = ChatPerplexity(model="sonar-pro", timeout=None).bind(
        extra_body={"search_recency_filter": "month"}
    )
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return response.content if isinstance(response.content, str) else str(response.content)
