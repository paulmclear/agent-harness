"""Perplexity sonar-pro research batch: opportunity signals.

Mirrors specs/hubspot-company-research/agents/research_batch_2_opportunity_signals.yaml
"""

from workflows.hubspot_company_research.agents._base import (
    RESEARCH_SYSTEM_PROMPT,
    make_research_batch_node,
)

USER_PROMPT = """Research {company_name} opportunity signals:

**Regulatory Pressure:**
- FCA thematic reviews affecting them
- Consultation papers they've responded to
- Remediation programmes
- Regulatory heat and immediate pressures

**Transformation Signals:**
- Job postings for Head of Financial Crime Transformation, Programme Managers
- Transformation-related hiring activity
- Required skills and project scope in job descriptions

**Operational Stress:**
- Transaction volume growth rates
- New products/services launched
- Market expansion or M&A activity
- Processing challenges and alert backlogs

**Cost Pressure:**
- Cost reduction programmes
- Efficiency initiatives and targets
- Earnings calls mentioning cost savings

Return structured JSON with fields: thematic_reviews (array), remediation_programs (array),
regulatory_heat_score (1-10), transformation_roles (array), capability_gaps (array),
volume_growth (object), operational_stress_score (1-10), cost_initiatives (array),
efficiency_targets (object), sources (array with url, title, publishedDate)."""


research_batch_2_node = make_research_batch_node(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    output_key="opportunity_signals_raw",
)
