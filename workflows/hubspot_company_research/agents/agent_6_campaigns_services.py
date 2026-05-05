"""Analyst 6: campaigns + services + value propositions (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_6_campaigns_services.yaml.
"""

from pydantic import BaseModel

from workflows.hubspot_company_research.agents._base import make_analyst_node

USER_PROMPT = """You are a campaign strategist matching company needs to service offerings.

**Company:** {company_name}
**Research Data:** {research_data}

**Task:** Recommend 3 campaigns, 5-7 service offerings, and 4-5 value propositions.

**Campaign Format:**
For each campaign provide:
- **Name:** (e.g., "Enterprise Financial-Crime Transformation")
- **Relevance Score:** X/10
- **Key Message:** One sentence pitch
- **Proof Points:** 3 case studies with metrics ("Tier-1 UK challenger: Reduced FCA actions from 24 to 3 in 18mo, cut false positives 45%")

**Service Recommendations:** (7-10 specific services)
- FCC Target Operating Model design & implementation
- AML/KYC policy framework uplift aligned to FCA/PRA
- Google Cloud transaction-monitoring model tuning
- US BSA/AML gap analysis and charter support
- Fraud-risk analytics and false-positive optimization
- Regulatory liaison & independent assurance
- Compliance training content for CMA order

**Value Propositions:** (4-5 compelling value statements)
- Reduce cost-to-income by automating FinCrime controls without compromising CX
- Secure regulator confidence and mitigate fines through proven remediation playbooks
- Accelerate US expansion with turnkey BSA/AML framework meeting OCC/FinCEN
- Free executive capacity with managed tuning services cutting alert noise 50%
- Demonstrate ROI with phased investment roadmap

**Output Format:**
- No tables"""


class Analyst6Output(BaseModel):
    campaigns: list[dict[str, object]]
    service_recommendations: list[str]
    value_propositions: list[str]


agent_6_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_6_campaigns",
    structured_output_model=Analyst6Output,
)
