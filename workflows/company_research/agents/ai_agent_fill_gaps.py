"""Tool-using gpt-5-mini agent that fills critical data gaps via Perplexity.

Mirrors specs/hubspot-company-research/agents/ai_agent_fill_gaps.yaml. The
n8n workflow binds a Perplexity sonar-pro tool to a LangChain agent loop;
here we use create_agent + the existing perplexity_search tool.
"""

from __future__ import annotations

import json

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from tools.perplexity_search_tool import perplexity_search
from workflows.company_research.state import AgentState

load_dotenv()

MODEL = "openai:gpt-5-mini"

SYSTEM_PROMPT = (
    "You are a research analyst specialized in finding accurate, up-to-date "
    "company information. Use your available tools to search for missing "
    "data. Always cite your sources with URLs."
)

USER_PROMPT = """You are a financial crime compliance research analyst finding missing data for {company_name}.

**Missing Critical Data:** {critical_gaps} critical gaps found

**Gap Details:**
{gaps}

**Instructions:**
1. For each missing field, use available search tools to find the most recent and accurate data
2. Prioritize critical gaps first
3. Return findings in JSON format with sources

**Output format:**
{{
  "filled_data": {{
    "field_name": {{"value": "data", "source": "url"}}
  }}
}}"""


_agent = create_agent(
    name="GapFillerAgent",
    system_prompt=SYSTEM_PROMPT,
    model=MODEL,
    tools=[perplexity_search],
)


def ai_agent_fill_gaps_node(state: AgentState) -> AgentState:
    formatted = USER_PROMPT.format(
        company_name=state.get("company_name") or "Unknown",
        critical_gaps=state.get("critical_gaps", 0),
        gaps=json.dumps(state.get("gaps") or [], indent=2),
    )
    try:
        output = _agent.invoke({"messages": [HumanMessage(content=formatted)]})
        state["filled_data"] = output["messages"][-1].content
    except Exception:
        state["filled_data"] = "{}"
    return state
