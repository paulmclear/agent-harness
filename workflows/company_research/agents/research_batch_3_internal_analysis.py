"""Perplexity sonar-pro research batch: internal compliance analysis.

Mirrors specs/hubspot-company-research/agents/research_batch_3_internal_analysis.yaml
"""

from workflows.company_research.agents._base import (
    RESEARCH_SYSTEM_PROMPT,
    make_research_batch_node,
)

USER_PROMPT = """Research {company_name} internal analysis:

**Financial Intelligence:**
- Compliance costs and budgets
- Cost-to-income ratio and efficiency metrics
- Regulatory remediation costs
- Recent fines or penalties

**Org Structure:**
- Compliance leadership (names, titles, LinkedIn, team sizes)
- Reporting lines (where compliance reports, levels to CEO)
- Team structure and geographic distribution

**Vendor Intelligence:**
- Current Big 4 engagements (PwC, EY, Deloitte, KPMG)
- Boutique financial crime consultancies
- Contract values and project examples

**Compliance Maturity:**
- Control framework assessments
- KYC/screening/sanctions system capabilities
- Audit findings and maturity ratings

**Peer Comparison:**
- UK financial services peers and competitors
- Technology adoption comparison
- Leading practices in peer group

Return structured JSON with fields: compliance_financials (object), efficiency_metrics (object),
compliance_leadership (array with name, title, linkedin_url, team_size), current_vendors (array),
vendor_spend_analysis (object), control_framework (object), system_capabilities (array),
peer_group (array), competitive_position, sources (array with url, title, publishedDate)."""


research_batch_3_node = make_research_batch_node(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    output_key="internal_analysis_raw",
)
