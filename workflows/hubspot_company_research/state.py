"""State for the HubSpot Company Research workflow.

Mirrors the n8n spec at specs/hubspot-company-research/workflow.yaml.
Trigger inputs flow in via `company_id` (and optionally `property_value`);
all subsequent stages append their outputs to this TypedDict, which is
shared across the StateGraph.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict


def _keep_first(x: Any, y: Any) -> Any:
    """Identity reducer: keep the first non-None value under concurrent writes."""
    return x if x is not None else y


class AgentState(TypedDict, total=False):
    # ── trigger inputs ────────────────────────────────────────────────
    company_id: str
    property_value: str  # value of `intelligence_report_status`

    # ── HubSpot company payload ───────────────────────────────────────
    company_properties: dict

    # ── prepared research context (set before fan-out 1) ─────────────
    company_name: Annotated[str, _keep_first]
    domain: Annotated[str, _keep_first]
    industry: Annotated[str, _keep_first]
    employees: Annotated[int, _keep_first]
    revenue: Annotated[float, _keep_first]
    location: Annotated[str, _keep_first]
    company_type: Annotated[str, _keep_first]
    is_public: Annotated[bool, _keep_first]

    # ── research batches (six concurrent writers, distinct keys) ──────
    corporate_intelligence_raw: str
    opportunity_signals_raw: str
    internal_analysis_raw: str
    relationship_intelligence_raw: str
    commercial_intelligence_raw: str
    strategic_assessment_raw: str

    # ── unified research data + citation registry ────────────────────
    research_data: Annotated[dict, _keep_first]
    citations: Annotated[list[dict], _keep_first]
    total_citations: Annotated[int, _keep_first]
    research_date: Annotated[str, _keep_first]

    # ── data-gap detection ────────────────────────────────────────────
    gaps: list[dict]
    total_gaps: int
    critical_gaps: int
    has_gaps: bool

    # ── gap-filler output (only set when has_gaps == True) ────────────
    filled_data: dict
    gaps_filled: int

    # ── analyst-agent outputs (seven concurrent writers) ──────────────
    agent_1_overview: str
    agent_2_regulatory: str
    agent_3_stakeholders: str
    agent_4_opportunity: str
    agent_5_scoring: str
    agent_6_campaigns: str
    agent_7_engagement: str

    # ── final report ──────────────────────────────────────────────────
    report_markdown: str
    report_html: str
    scoring_summary: dict

    # ── HubSpot writeback ─────────────────────────────────────────────
    hubspot_update_status: str

    # ── per-run output directory (e.g. output/2026-05-04_19-55-32) ────
    output_dir: Annotated[str, _keep_first]
