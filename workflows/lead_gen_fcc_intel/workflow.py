import datetime as dt
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from workflows.lead_gen_fcc_intel.agents.chief_intelligence_officer import (
    chief_intelligence_officer_node,
)
from workflows.lead_gen_fcc_intel.agents.enforcements import enforcement_risk_node
from workflows.lead_gen_fcc_intel.agents.growth_change import growth_change_node
from workflows.lead_gen_fcc_intel.agents.market_movement import market_movement_node
from workflows.lead_gen_fcc_intel.agents.regulatory_intelligence import (
    regulatory_intelligence_node,
)
from workflows.lead_gen_fcc_intel.format_report import format_report_node
from workflows.lead_gen_fcc_intel.state import AgentState

_ANALYSTS = (
    "regulatory_intelligence",
    "enforcement_risk",
    "growth_change",
    "market_movement",
)


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("regulatory_intelligence", regulatory_intelligence_node)
    builder.add_node("enforcement_risk", enforcement_risk_node)
    builder.add_node("growth_change", growth_change_node)
    builder.add_node("market_movement", market_movement_node)
    builder.add_node("chief_intelligence_officer", chief_intelligence_officer_node)
    builder.add_node("format_report", format_report_node)

    for analyst in _ANALYSTS:
        builder.add_edge(START, analyst)
        builder.add_edge(analyst, "chief_intelligence_officer")
    builder.add_edge("chief_intelligence_officer", "format_report")
    builder.add_edge("format_report", END)

    return builder.compile()


if __name__ == "__main__":
    run_dir = Path("output") / dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    graph = build_graph()
    final_state = graph.invoke({"output_dir": str(run_dir)})

    report = final_state.get("chief_intelligence_report", "No report generated.")
    (run_dir / "final_report.txt").write_text(report, encoding="utf-8")

    print(f"Run output written to: {run_dir}")
