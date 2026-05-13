"""Perplexity sonar-pro research batch: relationship intelligence.

Mirrors specs/hubspot-company-research/agents/research_batch_4_relationship_intelligence.yaml
"""

from workflows.company_research.agents._base import (
    RESEARCH_SYSTEM_PROMPT,
    make_research_batch_node,
)

USER_PROMPT = """Research {company_name} relationship intelligence:

**Event Intelligence:**
- Speaking engagements at conferences (2024-2025)
- Financial crime/compliance/RegTech events attended
- Industry association memberships

**Network Mapping:**
- Professional connections (via LinkedIn, shared employers)
- Industry association overlaps
- Potential introduction paths

**Engagement History:**
- Previous RFP participation with consultancies
- Past projects or business relationships
- Contract history with professional services firms

Return structured JSON with fields: upcoming_speaking (array with event_name, date,
speaker_name, topic), event_attendance (array), industry_associations (array),
mutual_connections (array with person_name, connection_type, shared_context),
previous_engagements (array with date, type, outcome), relationship_quality (object),
sources (array with url, title, publishedDate)."""


research_batch_4_node = make_research_batch_node(
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    output_key="relationship_intelligence_raw",
)
