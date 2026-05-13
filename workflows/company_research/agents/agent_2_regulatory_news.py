"""Analyst 2: regulatory status + recent news timeline (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_2_regulatory_news.yaml.
"""

from pydantic import BaseModel

from workflows.company_research.agents._base import make_analyst_node

USER_PROMPT = """You are a regulatory intelligence analyst tracking enforcement actions and corporate news timelines.

**Company:** {company_name}
**Research Data:** {research_data}
**Citations:** {citations}

**Task 1: Regulatory Status Summary**
Write 2-3 sentences covering:
- Active investigations (FCA, CMA, PRA, etc.) with status and next milestones
- Remediation commitments, deadlines, and progress (e.g., "CMA compliance training due March 2025")
- Regulatory risk level and current standing

**Task 2: Recent News Timeline**
Extract 5-8 dated news items (Mar 2024-present) in reverse chronological order:
- Product launches and regulatory approvals [citation]
- Leadership appointments and departures [citation]
- Regulatory actions, fines, enforcement notices [citation]
- Major strategic announcements (M&A, funding, market entry) [citation]
- Transformation programme milestones [citation]

**Output Format:**
- No tables"""

class Analyst2Output(BaseModel):
    regulatory_status: str
    recent_news: list[dict[str, str]]


agent_2_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_2_regulatory",
    structured_output_model=Analyst2Output,
)
