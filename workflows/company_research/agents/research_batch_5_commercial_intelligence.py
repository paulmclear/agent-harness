"""Perplexity sonar-pro research batch: commercial intelligence.

Mirrors specs/hubspot-company-research/agents/research_batch_5_commercial_intelligence.yaml
"""

from workflows.company_research.agents._base import (
    RESEARCH_SYSTEM_PROMPT,
    make_research_batch_node,
)

USER_PROMPT = """Research {company_name} commercial intelligence:

**Budget Intelligence:**
- Annual spend on professional services
- Compliance-related contract awards
- Procurement patterns and budget cycles

**Timeline Indicators:**
- Regulatory deadlines and compliance requirements
- Board-level commitments and transformation milestones
- Market pressures affecting timeline

**Competitor Intel:**
- PwC, EY, Deloitte, KPMG current engagements
- Recent financial crime projects by competitors
- Contract renewal timings
- Displacement opportunities

Return structured JSON with fields: consultancy_spend (object with annual_total,
compliance_portion, trend), budget_cycles (object), regulatory_deadlines (array with
requirement, deadline_date, current_readiness), transformation_milestones (array),
active_competitors (array with competitor_name, relationship_strength, contract_value,
renewal_timing), displacement_opportunities (array), sources (array with url, title,
publishedDate)."""


research_batch_5_node = make_research_batch_node(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    output_key="commercial_intelligence_raw",
)
