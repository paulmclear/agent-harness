"""Perplexity sonar-pro research batch: corporate intelligence.

Mirrors specs/hubspot-company-research/agents/research_batch_1_corporate_intelligence.yaml
"""

from workflows.company_research.agents._base import (
    RESEARCH_SYSTEM_PROMPT,
    make_research_batch_node,
)

USER_PROMPT = """Research {company_name} corporate intelligence:

**Corporate Overview:**
- Annual revenue: Return as NUMBER ONLY in billions (e.g., 1.2 for £1.2bn), currency code (GBP/USD), and year
- Employee count: Return as NUMBER ONLY (e.g., 2500 not "2,500 employees")
- Geographic presence (regions, offices, key locations, regulated entities)
- Recent acquisitions (last 2 years with dates, values, strategic rationale)

**Regulatory Status:**
- FCA enforcement notices, Dear CEO letters, skilled person appointments
- Regulatory findings in last 12 months
- Regulatory actions and remediation status

**Leadership:**
- Chief Risk Officer, MLRO, Head of Financial Crime, Head of Compliance
- Names, previous employers, LinkedIn profiles, tenure
- Recent appointments (2024-2025) and departures

Return structured JSON with fields:
- company_name: string
- annual_revenue: {{amount: number (e.g. 1.2), currency: "GBP"|"USD", year: number}}
- employee_count: number (e.g. 2500)
- geographic_presence: array
- recent_acquisitions: array
- regulatory_actions: array
- regulatory_risk_score: number|null
- leadership_team: array with name, title, linkedin_url, tenure, background
- sources: array with url, title, publishedDate

CRITICAL: annual_revenue.amount and employee_count MUST be numbers, not strings."""


research_batch_1_node = make_research_batch_node(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    output_key="corporate_intelligence_raw",
)
