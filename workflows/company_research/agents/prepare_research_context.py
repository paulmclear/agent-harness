"""Tavily + gpt-5-mini agent that resolves a company name to structured metadata.

Step 1: Tavily search for company facts.
Step 2: gpt-5-mini extracts structured fields via .with_structured_output().
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr
from tavily import TavilyClient

from workflows.company_research.state import AgentState

load_dotenv()

_tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


class _CompanyProfile(BaseModel):
    name: str = Field(description="Official full company name")
    domain: str = Field(description="Primary website domain, e.g. acme.com (no https://)")
    industry: str = Field(description="Primary industry sector")
    numberofemployees: int = Field(description="Approximate global employee count (0 if unknown)")
    annualrevenue: float = Field(description="Approximate annual revenue in USD (0 if unknown)")
    city: str = Field(description="Headquarters city")
    country: str = Field(description="Headquarters country")


_EXTRACT_SYSTEM = (
    "You are a business research analyst. Extract company facts from the provided search results. "
    "Use 0 for numeric fields when data is unavailable."
)


def prepare_research_context_node(state: AgentState) -> AgentState:
    company_name = (state.get("company_name") or "").strip()
    if not company_name:
        raise ValueError("prepare_research_context_node: company_name is required")

    employees = 0
    revenue = 0.0

    try:
        results = _tavily.search(
            f"{company_name} company headquarters employees annual revenue industry",
            max_results=5,
        )
        snippets = "\n\n".join(
            f"[{r['title']}]\n{r['content']}" for r in results.get("results", [])
        )

        api_key = os.environ.get("OPENAI_API_KEY")
        llm = ChatOpenAI(
            model="gpt-5-mini",
            api_key=SecretStr(api_key) if api_key else None,
        ).with_structured_output(_CompanyProfile, strict=False)

        profile: _CompanyProfile = llm.invoke([
            SystemMessage(content=_EXTRACT_SYSTEM),
            HumanMessage(content=f"Company: {company_name}\n\nSearch results:\n{snippets}"),
        ])

        employees = profile.numberofemployees
        revenue = profile.annualrevenue
        state["company_name"] = profile.name or company_name
        state["domain"] = profile.domain
        state["industry"] = profile.industry
        state["location"] = ", ".join(p for p in (profile.city, profile.country) if p)
    except Exception:
        pass  # proceed with defaults; company_name remains as supplied

    if employees > 1000:
        company_type = "large"
    elif employees > 250:
        company_type = "medium"
    else:
        company_type = "small"

    state["employees"] = employees
    state["revenue"] = revenue
    state["company_type"] = company_type
    state["is_public"] = revenue > 100_000_000
    return state
