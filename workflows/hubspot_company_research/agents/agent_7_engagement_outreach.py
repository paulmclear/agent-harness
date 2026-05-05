"""Analyst 7: engagement strategy + outreach templates (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_7_engagement_outreach.yaml.
"""

from pydantic import BaseModel

from workflows.hubspot_company_research.agents._base import make_analyst_node

USER_PROMPT = """You are an outreach specialist crafting personalized engagement strategies and templates.

**Company:**

{company_name}

**Research Data:**

{research_data}

---

**Task:** Create comprehensive engagement plan with templates.

**1. Engagement Strategy Summary** (3-4 sentences)
- Primary target executive and why
- Entry strategy (discovery call focus)
- Service alignment (which campaigns/services lead)
- Key value proposition (one sentence)

**2. Target Contacts List:**
Name
Title
LinkedIn
Relevance

**3. Outreach Templates:**

**Email Option 1:**
- Subject: (compelling, specific)
- Opening Hook: (1 sentence - personalized)
- Context Bridge: (1-2 sentences - show research)
- Value Statement: (1 sentence with metric)
- Call to Action: (specific ask with timeframe)

**Email Option 2:** (Different angle - e.g., regulatory thematic)

**LinkedIn Message:** (50-75 words, conversational)

**Call Script:**
- Opening: (20 words)
- Value Hook: (1 sentence with proof)
- Engagement Question: (open-ended)
- Next Steps: (3 options: interested / not now / wrong person)

**4. Follow-up Sequence:** (4 touches)
- Touch 2: Case study email (7 days later)
- Touch 3: LinkedIn InMail about hiring gap (14 days)
- Touch 4: Final value-add touchpoint (21 days)

**Output Format:**
- No tables"""


class Analyst7Output(BaseModel):
    engagement_strategy: dict[str, str]
    target_contacts: list[dict[str, str]]
    email_templates: list[dict[str, object]]
    linkedin_message: str
    call_script: dict[str, object]
    followup_sequence: list[dict[str, object]]


agent_7_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_7_engagement",
    structured_output_model=Analyst7Output,
)
