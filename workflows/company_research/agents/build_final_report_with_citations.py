"""Final report builder agent (gpt-5.1, low reasoning effort).

Mirrors specs/hubspot-company-research/agents/build_final_report_with_citations.yaml.
Consumes the unified researchData plus the seven analyst-agent outputs and
returns a JSON object containing the full markdown report.
"""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from workflows.company_research.state import AgentState

load_dotenv()

MODEL = "gpt-5.1"

USER_PROMPT = """You are an intelligent report builder. Build a comprehensive markdown report from research data and agent outputs.

**RAW RESEARCH DATA (from Perplexity):**
{research_data}

**AGENT ANALYSIS OUTPUTS:**
Agent 1 (Overview): {agent_1}
Agent 2 (Regulatory): {agent_2}
Agent 3 (Stakeholders): {agent_3}
Agent 4 (Opportunity): {agent_4}
Agent 5 (Scoring): {agent_5}
Agent 6 (Campaigns): {agent_6}
Agent 7 (Engagement): {agent_7}

**YOUR TASK:**

1. **Extract company data intelligently from researchData.corporate_intelligence:**
   - Revenue: Extract and format cleanly (e.g., if you see {{amount: "£1.2 billion", currency: "GBP", year: "2025"}}, output "£1.2bn (2025)")
   - Employees: Extract employee count as number or formatted string
   - Industry: Extract industry/sector

2. **Parse agent outputs:** Each agent returned JSON - extract the data intelligently

3. **Build markdown report** with these sections:
   - Company overview (with Revenue/Employees extracted)
   - Key findings
   - Regulatory status
   - Recent news
   - Key stakeholders
   - Opportunity assessment
   - Scoring analysis
   - Recommended campaigns
   - Service recommendations
   - Value propositions
   - Engagement strategy
   - Outreach templates
   - Sources (bibliography from citations)

**CRITICAL INSTRUCTIONS:**
- Be INTELLIGENT about data extraction - handle ANY format
- For revenue: "£1.2 billion" should become "£1.2bn"
- For employees: Return the NUMBER if found, otherwise "N/A"
- Parse agent JSON outputs properly
- NO TABLES
- Include all citations

Citations registry: {citations}
companyId: {company_id}
companyName: {company_name}
totalCitations: {total_citations}
researchDate: {research_date}

**RETURN JSON:**
{{
  "report": "# {company_name} - Report\\n\\n## Company overview\\n\\n**Revenue:** ...\\n**Employees:** ...\\n...",
  "companyId": "{company_id}",
  "companyName": "{company_name}",
  "scoring": {{"overall_score": 87, "overall_priority": "Hot"}},
  "totalCitations": {total_citations},
  "researchDate": "{research_date}"
}}"""


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _build_llm() -> ChatOpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    return ChatOpenAI(
        model=MODEL,
        api_key=SecretStr(api_key) if api_key else None,
        reasoning={"effort": "low"},
    )


def _parse_builder_output(text: str) -> dict:
    stripped = text.strip()
    candidates: list[str] = []
    if stripped.startswith("{"):
        candidates.append(stripped)
    match = _JSON_FENCE.search(stripped)
    if match:
        candidates.append(match.group(1))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    # Treat the entire response as the markdown report when JSON parsing fails.
    return {"report": text}


def build_final_report_node(state: AgentState) -> AgentState:
    formatted = USER_PROMPT.format(
        research_data=json.dumps(state.get("research_data") or {}, indent=2),
        citations=json.dumps(state.get("citations") or [], indent=2),
        agent_1=state.get("agent_1_overview") or "",
        agent_2=state.get("agent_2_regulatory") or "",
        agent_3=state.get("agent_3_stakeholders") or "",
        agent_4=state.get("agent_4_opportunity") or "",
        agent_5=state.get("agent_5_scoring") or "",
        agent_6=state.get("agent_6_campaigns") or "",
        agent_7=state.get("agent_7_engagement") or "",
        company_id=state.get("company_id") or "",
        company_name=state.get("company_name") or "Unknown",
        total_citations=state.get("total_citations", 0),
        research_date=state.get("research_date") or "",
    )

    try:
        llm = _build_llm()
        response = llm.invoke([HumanMessage(content=formatted)])
        raw = response.content if isinstance(response.content, str) else str(response.content)
    except Exception:
        raw = f"# {state.get('company_name') or 'Unknown'} - Research Report\n\n*Report generation failed.*"

    parsed = _parse_builder_output(raw)
    state["report_markdown"] = parsed.get("report") or raw
    if isinstance(parsed.get("scoring"), dict):
        state["scoring_summary"] = parsed["scoring"]
    return state
