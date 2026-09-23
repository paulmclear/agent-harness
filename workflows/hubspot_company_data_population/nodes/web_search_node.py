from typing import Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.messages import HumanMessage
from langchain_core.tools import tool

from tools.search_tool import internet_search
from workflows.hubspot_company_data_population.nodes.classifier_agent_node import load_system_prompt
from workflows.hubspot_company_data_population.state import (
    AgentState,
    CompanyClassificationOutput,
)


load_dotenv()

CONFIDENCE_THRESHOLD = 0.5
MAX_SEARCHES = 1

WEB_SEARCH_PREAMBLE = f"""
The previous classification attempt returned low confidence. You may call the
`internet_search` tool AT MOST {MAX_SEARCHES} time(s). Plan a single, specific
query that will most efficiently disambiguate the company (e.g. the company
name plus a qualifier like "official site", "regulator", or jurisdiction).
After that one search, produce your final classification — do not attempt
additional searches.

Cite the strongest evidence in the `rationale`. Only return high confidence
(>= 0.8) if the evidence is direct and authoritative.
"""


def _build_capped_search_tool():
    """Return a fresh `internet_search` tool whose call budget is enforced per node invocation."""
    remaining = {"count": MAX_SEARCHES}

    @tool
    def internet_search_capped(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False,
    ) -> str:
        """Run a web search. Limited to a single call per classification attempt."""
        if remaining["count"] <= 0:
            return (
                "ERROR: Search budget exhausted for this classification. "
                "Produce your final structured answer now using the evidence you already have."
            )
        remaining["count"] -= 1
        return internet_search(
            query=query,
            max_results=max_results,
            topic=topic,  # type: ignore[arg-type]
            include_raw_content=include_raw_content,
        )

    return internet_search_capped


def _build_agent():
    return create_agent(
        model="openai:gpt-5-mini",
        system_prompt=load_system_prompt() + WEB_SEARCH_PREAMBLE,
        tools=[_build_capped_search_tool()],
        response_format=ProviderStrategy(CompanyClassificationOutput),
    )


def needs_web_search_router(state: AgentState) -> str:
    classification = state.get("classification")
    if classification is None:
        return "web_search"
    if classification.confidence < CONFIDENCE_THRESHOLD:
        return "web_search"
    return "done"


def web_search_node(state: AgentState) -> dict:
    company_name = state.get("company_name", "")
    if not company_name:
        return {"classification": state.get("classification")}

    prior = state.get("classification")
    prior_block = ""
    if prior is not None:
        prior_block = (
            f"\n\nPrior low-confidence attempt "
            f"(confidence={prior.confidence:.2f}):\n"
            f"  sector: {prior.sector}\n"
            f"  sub_sector: {prior.sub_sector}\n"
            f"  rationale: {prior.rationale}"
        )

    message = HumanMessage(
        content=(
            f"Classify the following company into a sector: {company_name}."
            f"{prior_block}"
        )
    )

    # Fresh agent + fresh budget per invocation — the cap must not leak across companies.
    agent = _build_agent()
    response = agent.invoke({"messages": [message]})
    return {"classification": response["structured_response"]}
