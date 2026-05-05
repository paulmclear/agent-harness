"""LangGraph wiring for the HubSpot Company Research workflow.

Mirrors specs/hubspot-company-research/workflow.yaml:
  trigger → check_status_value (router) → get_company_data
   → prepare_research_context
   → fan_out [6 perplexity batches] → merge
   → extract_deduplicate_citations → detect_data_gaps
   → has_gaps (router) → ai_agent_fill_gaps + merge_gap_data
                       \\— no_gaps_pass_through
   → fan_out [7 analyst agents] → merge
   → build_final_report_with_citations
   → convert_markdown_to_html → update_hubspot_record → format_report → END
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from workflows.hubspot_company_research.agents.agent_1_overview_findings import (
    agent_1_node,
)
from workflows.hubspot_company_research.agents.agent_2_regulatory_news import (
    agent_2_node,
)
from workflows.hubspot_company_research.agents.agent_3_stakeholder_analysis import (
    agent_3_node,
)
from workflows.hubspot_company_research.agents.agent_4_opportunity_assessment import (
    agent_4_node,
)
from workflows.hubspot_company_research.agents.agent_5_detailed_scoring import (
    agent_5_node,
)
from workflows.hubspot_company_research.agents.agent_6_campaigns_services import (
    agent_6_node,
)
from workflows.hubspot_company_research.agents.agent_7_engagement_outreach import (
    agent_7_node,
)
from workflows.hubspot_company_research.agents.ai_agent_fill_gaps import (
    ai_agent_fill_gaps_node,
)
from workflows.hubspot_company_research.agents.build_final_report_with_citations import (
    build_final_report_node,
)
from workflows.hubspot_company_research.agents.research_batch_1_corporate_intelligence import (
    research_batch_1_node,
)
from workflows.hubspot_company_research.agents.research_batch_2_opportunity_signals import (
    research_batch_2_node,
)
from workflows.hubspot_company_research.agents.research_batch_3_internal_analysis import (
    research_batch_3_node,
)
from workflows.hubspot_company_research.agents.research_batch_4_relationship_intelligence import (
    research_batch_4_node,
)
from workflows.hubspot_company_research.agents.research_batch_5_commercial_intelligence import (
    research_batch_5_node,
)
from workflows.hubspot_company_research.agents.research_batch_6_strategic_assessment import (
    research_batch_6_node,
)
from workflows.hubspot_company_research.format_report import format_report_node
from workflows.hubspot_company_research.hubspot_io import (
    get_company_data_node,
    update_hubspot_record_node,
)
from workflows.hubspot_company_research.state import AgentState
from workflows.hubspot_company_research.transforms import (
    convert_markdown_to_html_node,
    detect_data_gaps_node,
    extract_deduplicate_citations_node,
    merge_gap_data_node,
    no_gaps_pass_through_node,
    prepare_research_context_node,
)

_RESEARCH_BATCHES = (
    ("research_batch_1", research_batch_1_node),
    ("research_batch_2", research_batch_2_node),
    ("research_batch_3", research_batch_3_node),
    ("research_batch_4", research_batch_4_node),
    ("research_batch_5", research_batch_5_node),
    ("research_batch_6", research_batch_6_node),
)

_ANALYSTS = (
    ("agent_1_overview", agent_1_node),
    ("agent_2_regulatory", agent_2_node),
    ("agent_3_stakeholders", agent_3_node),
    ("agent_4_opportunity", agent_4_node),
    ("agent_5_scoring", agent_5_node),
    ("agent_6_campaigns", agent_6_node),
    ("agent_7_engagement", agent_7_node),
)


def _check_status_value(state: AgentState) -> str:
    """Router: skip the run if intelligence_report_status is already 'Updated'."""
    if (state.get("property_value") or "") == "Updated":
        return "skip"
    return "continue"


def _has_gaps(state: AgentState) -> str:
    return "fill_gaps" if state.get("has_gaps") else "skip_gaps"


WORKFLOW_NAME = "hubspot_company_research"

_OUTPUT_KEYS = (
    "report_markdown",
    "scoring_summary",
    "hubspot_update_status",
    "total_citations",
    "formatted_report_path",
)


def run_workflow(registry, graph, run_id: str, inputs: dict):
    registry.mark_running(run_id)
    try:
        state = graph.invoke(inputs, config={"configurable": {"thread_id": run_id}})
        outputs = {k: state.get(k) for k in _OUTPUT_KEYS}
        registry.complete_run(run_id, outputs)
        return state
    except Exception as exc:
        registry.fail_run(run_id, str(exc))
        raise


def _print_runs(runs: list) -> None:
    if not runs:
        print("No runs found.")
        return
    header = f"{'RUN_ID':<36}  {'SUBJECT':<14}  {'STATUS':<10}  {'ATT':>3}  {'CREATED':<26}  ERROR"
    print(header)
    print("-" * (len(header) + 10))
    for r in runs:
        error = (r.error or "")[:50]
        print(
            f"{r.run_id:<36}  {r.subject:<14}  {r.status:<10}  {r.attempt:>3}"
            f"  {r.created_at:<26}  {error}"
        )


def build_graph(checkpointer=None):
    builder = StateGraph(AgentState)

    builder.add_node("get_company_data", get_company_data_node)
    builder.add_node("prepare_research_context", prepare_research_context_node)

    for name, node in _RESEARCH_BATCHES:
        builder.add_node(name, node)

    builder.add_node("extract_deduplicate_citations", extract_deduplicate_citations_node)
    builder.add_node("detect_data_gaps", detect_data_gaps_node)
    builder.add_node("ai_agent_fill_gaps", ai_agent_fill_gaps_node)
    builder.add_node("merge_gap_data", merge_gap_data_node)
    builder.add_node("no_gaps_pass_through", no_gaps_pass_through_node)

    for name, node in _ANALYSTS:
        builder.add_node(name, node)

    builder.add_node("build_final_report", build_final_report_node)
    builder.add_node("convert_markdown_to_html", convert_markdown_to_html_node)
    builder.add_node("update_hubspot_record", update_hubspot_record_node)
    builder.add_node("format_report", format_report_node)

    # ── trigger guard: skip when status is already "Updated" ──────────
    builder.add_conditional_edges(
        START,
        _check_status_value,
        {"continue": "get_company_data", "skip": END},
    )

    builder.add_edge("get_company_data", "prepare_research_context")

    # ── fan-out to six concurrent research batches, fan-in to extract ─
    for name, _ in _RESEARCH_BATCHES:
        builder.add_edge("prepare_research_context", name)
        builder.add_edge(name, "extract_deduplicate_citations")

    builder.add_edge("extract_deduplicate_citations", "detect_data_gaps")

    # ── conditional gap-fill branch ───────────────────────────────────
    builder.add_conditional_edges(
        "detect_data_gaps",
        _has_gaps,
        {
            "fill_gaps": "ai_agent_fill_gaps",
            "skip_gaps": "no_gaps_pass_through",
        },
    )
    builder.add_edge("ai_agent_fill_gaps", "merge_gap_data")

    # ── fan-out to seven concurrent analysts (both branches converge) ─
    for name, _ in _ANALYSTS:
        builder.add_edge("merge_gap_data", name)
        builder.add_edge("no_gaps_pass_through", name)
        builder.add_edge(name, "build_final_report")

    builder.add_edge("build_final_report", "convert_markdown_to_html")
    builder.add_edge("convert_markdown_to_html", "update_hubspot_record")
    builder.add_edge("update_hubspot_record", "format_report")
    builder.add_edge("format_report", END)

    return builder.compile(checkpointer=checkpointer)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the HubSpot Company Research workflow")
    parser.add_argument("company_id", nargs="?", help="HubSpot company ID (fresh run)")
    parser.add_argument("--resume", metavar="RUN_ID", help="Resume a FAILED or RUNNING run by ID")
    parser.add_argument("--list-runs", action="store_true", help="List recent runs for this workflow")
    parser.add_argument("--status", help="Filter --list-runs by status: PENDING, RUNNING, COMPLETED, FAILED")
    parser.add_argument(
        "--property-value",
        default="Requested",
        help="Simulated value of intelligence_report_status (default: 'Requested')",
    )
    return parser.parse_args()


if __name__ == "__main__":
    from harness.checkpoint import make_sync_saver
    from harness.run_registry import FAILED, RUNNING, RunRegistry

    args = _parse_args()

    db_path = Path(os.getenv("RUNS_DB_PATH", "output/runs.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    registry = RunRegistry(db_path)

    if args.list_runs:
        runs = registry.list_runs(workflow=WORKFLOW_NAME, status=args.status or None)
        _print_runs(runs)
        sys.exit(0)

    if args.resume:
        run = registry.get_run(args.resume)
        if not run:
            print(f"Run not found: {args.resume}", file=sys.stderr)
            sys.exit(1)
        if run.status not in {FAILED, RUNNING}:
            print(
                f"Cannot resume: status is '{run.status}'. Only FAILED or RUNNING runs are resumable.",
                file=sys.stderr,
            )
            sys.exit(1)
        saver = make_sync_saver(db_path)
        graph = build_graph(checkpointer=saver)
        final_state = run_workflow(registry, graph, args.resume, run.inputs)
        print(f"Run {args.resume} completed.")
        print(f"HubSpot update status: {final_state.get('hubspot_update_status') or 'skipped'}")
        sys.exit(0)

    if not args.company_id:
        print(
            "Error: provide a company_id for a fresh run, --resume RUN_ID, or --list-runs.",
            file=sys.stderr,
        )
        sys.exit(1)

    run_dir = Path("output") / dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    inputs = {
        "company_id": args.company_id,
        "property_value": args.property_value,
        "output_dir": str(run_dir),
    }
    run = registry.create_run(WORKFLOW_NAME, args.company_id, inputs)
    saver = make_sync_saver(db_path)
    graph = build_graph(checkpointer=saver)
    final_state = run_workflow(registry, graph, run.run_id, inputs)
    print(f"Run {run.run_id} complete. Output written to: {run_dir}")
    print(f"HubSpot update status: {final_state.get('hubspot_update_status') or 'skipped'}")
