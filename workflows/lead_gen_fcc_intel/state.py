from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class AgentState(TypedDict, total=False):
    # analyst outputs (written by analyst nodes, read by chief intelligence officer)
    regulatory_intelligence_analysis: dict
    enforcement_risk_analysis: dict
    market_movement_analysis: dict
    growth_change_analysis: dict

    # final report
    chief_intelligence_report: str
    formatted_report_path: str

    # per-run output directory (e.g. output/2026-05-04_19-55-32)
    # Annotated with identity reducer to allow pass-through in concurrent nodes
    output_dir: Annotated[str, lambda x, y: x or y]
