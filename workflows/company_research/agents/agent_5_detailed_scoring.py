"""Analyst 5: detailed lead scoring across ICP/Warmth/Campaign/Persona (gpt-5-mini).

Mirrors specs/hubspot-company-research/agents/agent_5_detailed_scoring.yaml.
Note: spec input excludes citations, but the shared analyst factory always
provides them; the prompt simply doesn't reference {citations}.
"""

from pydantic import BaseModel

from workflows.company_research.agents._base import make_analyst_node

USER_PROMPT = """You are a lead scoring analyst providing detailed justification for ICP/Warmth/Campaign/Persona scores.

**Company:** {company_name}
**Research Data:** {research_data}

**Scoring Framework:**
- **ICP Score (0-25):** How well does company match Ideal Customer Profile? (regulated finserv, £0.5-5bn revenue, 1k-10k employees, active regulatory pressure, transformation underway, identified stakeholders)
- **Warmth Score (0-25):** How urgent is the need? (active investigations, deadlines, budget allocated, hiring signals, pain points quantified)
- **Campaign Score (0-25):** How well do our campaigns align? (financial crime transformation, fraud optimization, US expansion, alert reduction)
- **Persona Score (0-25):** Can we reach decision-makers? (executives identified, contact info available, warm intro paths, engagement opportunities)

**Task 1: Score Calculation**
Calculate scores with justification

**Task 2: ICP Matching List**

Criterion
Evidence
Strength

**Task 3: Missing Criteria** (what prevents perfect score)

**Output Format:**
- No tables"""


class Analyst5Output(BaseModel):
    overall_score: int
    overall_priority: str
    breakdown: list[dict[str, object]]
    icp_matching: list[dict[str, str]]
    missing_criteria: list[str]


agent_5_node = make_analyst_node(
    user_prompt=USER_PROMPT,
    output_key="agent_5_scoring",
    structured_output_model=Analyst5Output,
)
