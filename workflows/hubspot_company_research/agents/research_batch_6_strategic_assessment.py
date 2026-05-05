"""Perplexity sonar-pro research batch: strategic assessment.

Mirrors specs/hubspot-company-research/agents/research_batch_6_strategic_assessment.yaml
"""

from workflows.hubspot_company_research.agents._base import (
    RESEARCH_SYSTEM_PROMPT,
    make_research_batch_node,
)

USER_PROMPT = """Research {company_name} strategic assessment:

**Executive Priorities:**
- CEO, CRO, CFO quotes and speeches
- Financial crime and compliance priorities mentioned
- Regulatory relationship goals
- Operational efficiency mandates

**Pain Point Validation:**
- Alert volumes and false positive rates (with specific numbers)
- KYC backlogs
- Screening system performance issues
- Quantified compliance operations challenges

**Cultural Fit:**
- Stated values and leadership principles
- Decision-making style
- Approach to innovation and external partnerships
- Change management approach

Return structured JSON with fields: executive_statements (array with executive_name, role,
statement, priorities_revealed), strategic_priorities (array), operational_pain_points
(array with pain_point, severity, business_impact, metrics), system_performance (array),
organizational_values (array), leadership_style (object with decision_style, change_approach),
sources (array with url, title, publishedDate)."""


research_batch_6_node = make_research_batch_node(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    output_key="strategic_assessment_raw",
)
