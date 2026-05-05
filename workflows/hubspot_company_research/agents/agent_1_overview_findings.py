"""Analyst 1: company overview narrative + key findings (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_1_overview_findings.yaml.
"""
from pydantic import BaseModel

from workflows.hubspot_company_research.agents._base import make_analyst_node

USER_PROMPT = """You are a business intelligence analyst crafting comprehensive company overview narratives with inline citations.

**Company:** {company_name}
**Research Data:** {research_data}
**Citations Available:** {citations}

**Task:** Generate a detailed Company Overview section (3-5 paragraphs) and Key Findings (5-7 bullet points) using inline citations [1], [2], etc.

**Company Overview Requirements:**
- Paragraph 1: Company identity, industry position, core business model, revenue/employee scale with citations
- Paragraph 2: Geographic footprint, market expansion, recent strategic moves (M&A, new products) with citations
- Paragraph 3: Regulatory environment, compliance posture, current regulatory pressures/investigations with citations
- Paragraph 4 (if applicable): Technology infrastructure, innovation approach, competitive differentiators
- Paragraph 5 (if applicable): Strategic priorities and transformation initiatives

**Key Findings Requirements:**
- Revenue growth metrics with YoY % and absolute figures [citation]
- Active regulatory investigations, enforcement actions, remediation status [citation]
- Major transformation programmes, compliance initiatives, timelines [citation]
- Operational pain points: AML false positives %, KYC backlogs, alert volumes [citation]
- Strategic expansion plans: new markets, products, regulatory approvals [citation]
- Technology investments: fraud detection improvements, automation gains [citation]
- Cost pressures and efficiency targets from earnings calls [citation]

**Output Format:**
- No tables"""

class Analyst1Output(BaseModel):
    company_overview: str
    key_findings: list[str]


agent_1_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_1_overview",
    structured_output_model=Analyst1Output,
)
