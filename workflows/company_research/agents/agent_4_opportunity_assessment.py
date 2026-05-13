"""Analyst 4: opportunity strength assessment (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_4_opportunity_assessment.yaml.
"""

from pydantic import BaseModel

from workflows.company_research.agents._base import make_analyst_node

USER_PROMPT = """You are a business development analyst assessing sales opportunities and buying signals.

**Company:** {company_name}
**Research Data:** {research_data}
**Citations:** {citations}

**Task:** Assess opportunity strength across multiple dimensions:

**1. Primary Trigger** (1-2 sentences)
What is the main event/pressure driving immediate need?

**2. Key Signals List:**
Signal Type
Confidence
Evidence
Timing

**3. Budget Indicators** (3-5 bullets)
- Dedicated programme funding amounts/evidence [citation]
- Recent fundraising providing capital for initiatives [citation]
- Procurement patterns and budget cycles [citation]

**4. Competitive Activity** (2-4 bullets)
- Current Big 4/consultancy engagements [citation]
- Technology partnerships (Google Cloud, SAP, etc.) [citation]
- Conference participation showing openness to vendors [citation]

**Output Format:**
- No tables"""

class Analyst4Output(BaseModel):
    primary_trigger: str
    key_signals: list[dict[str, str]]
    budget_indicators: list[str]
    competitive_activity: list[str]


agent_4_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_4_opportunity",
    structured_output_model=Analyst4Output,
)
