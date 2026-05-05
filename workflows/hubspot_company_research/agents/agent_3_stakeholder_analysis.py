"""Analyst 3: stakeholder profiles (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_3_stakeholder_analysis.yaml.
"""

from pydantic import BaseModel

from workflows.hubspot_company_research.agents._base import make_analyst_node

USER_PROMPT = """You are an executive stakeholder analyst profiling decision-makers and their priorities.

**Company:** {company_name}
**Research Data:** {research_data}
**Citations:** {citations}

**Task:** Identify 4-6 key executives (CEO, CFO, CRO, Head of Financial Crime, MLRO, etc.) and provide:

**1. Executive Leadership List:**
Name
Title
Influence
Key Information
[citations]

**2. Detailed Stakeholder Profiles** (for top 3 executives):
For each executive provide:
- **Priorities:** 3-4 bullet points on their current focus areas
- **Challenges:** 3-4 key obstacles they face
- **Engagement Preferences:** How they prefer to receive information and make decisions

**Output Format:**
- No tables"""

class Analyst3Output(BaseModel):
    executive_table: list[dict[str, str]]
    stakeholder_profiles: list[dict[str, object]]


agent_3_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_3_stakeholders",
    structured_output_model=Analyst3Output,
)
