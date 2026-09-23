"""l2 workflow graph and CLI.

Run from the repo root:
    uv run python -m workflows.practice.l2.graph --execute                # triage every sample ticket
    uv run python -m workflows.practice.l2.graph --execute --ticket T002  # one sample ticket
    uv run python -m workflows.practice.l2.graph --debug                  # dry run, no agent calls*
    uv run python -m workflows.practice.l2.graph --output-image           # write graph.png

*Debug skips the LangChain agents only; the TypeSafe nodes still call TypeSafe.
"""

import argparse
import logging
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.nodes.classify_security_risk_node import (
    classify_security_risk_node,
    requires_security_escalation,
)
from workflows.practice.l2.nodes.classify_ticket_node import classify_ticket_node
from workflows.practice.l2.nodes.grade_articles_node import (
    grade_articles_node,
    route_after_grading,
)
from workflows.practice.l2.nodes.kb_lookup_node import kb_lookup_node
from workflows.practice.l2.nodes.populate_ticket_details_node import (
    populate_ticket_details_node,
)
from workflows.practice.l2.agents.kb_search_agent import kb_search_agent_node
from workflows.practice.l2.agents.triage_agent import triage_agent_node
from workflows.practice.l2.nodes.build_triage_output_node import (
    build_triage_output_node,
)
from workflows.practice.l2.nodes.security_handoff_node import security_handoff_node
from workflows.practice.l2.state import InputState, State
from workflows.practice.l2.models import SupportTicket


logger = logging.getLogger(__name__)

GRAPH_IMAGE_PATH = Path(__file__).parent / "graph.png"

SAMPLE_TICKETS = [
    SupportTicket(
        ticket_id="T001",
        employee_id="E001",
        subject="Lost Device",
        description="My device was lost yesterday.",
    ),
    SupportTicket(
        ticket_id="T002",
        employee_id="E002",
        subject="Forgot password",
        description="How can I reset my password?",
    ),
    SupportTicket(
        ticket_id="T003",
        employee_id="E003",
        subject="VPN keeps dropping",
        description="The VPN disconnects every few minutes when I work from home.",
    ),
    # vague wording: the first keyword search tends to miss, exercising kb_search_agent
    SupportTicket(
        ticket_id="T004",
        employee_id="E004",
        subject="Can't get in",
        description="Tried a few times this morning and now it just says wait 30 minutes.",
    ),
]


def build_graph(output_image: bool = False) -> CompiledStateGraph:
    builder = StateGraph(State, input_schema=InputState)

    # nodes
    builder.add_node("populate_ticket_details", populate_ticket_details_node)
    builder.add_node("classify_security_risk", classify_security_risk_node)
    builder.add_node("classify_ticket", classify_ticket_node)
    builder.add_node("kb_lookup", kb_lookup_node)
    builder.add_node("grade_articles", grade_articles_node)
    builder.add_node("security_handoff", security_handoff_node)
    builder.add_node("kb_search_agent", kb_search_agent_node)
    builder.add_node("triage_agent", triage_agent_node)
    builder.add_node("build_triage_output", build_triage_output_node)

    # edges
    builder.add_edge(START, "populate_ticket_details")
    builder.add_edge("populate_ticket_details", "classify_security_risk")

    # if security related, immediately handoff
    builder.add_conditional_edges(
        "classify_security_risk",
        requires_security_escalation,
        ["security_handoff", "classify_ticket"],
    )

    # ordinary path: always search the KB, then grade candidates (ADR-001)
    builder.add_edge("classify_ticket", "kb_lookup")
    builder.add_edge("kb_lookup", "grade_articles")
    builder.add_conditional_edges(
        "grade_articles",
        route_after_grading,
        ["triage_agent", "kb_search_agent", "build_triage_output"],
    )
    # escalation: the agent's picks are regraded by the same judge
    builder.add_edge("kb_search_agent", "grade_articles")
    builder.add_edge("triage_agent", "build_triage_output")

    # final positions
    builder.add_edge("build_triage_output", END)
    builder.add_edge("security_handoff", END)

    # compile
    graph = builder.compile()

    if output_image:
        GRAPH_IMAGE_PATH.write_bytes(graph.get_graph(xray=True).draw_mermaid_png())
        logger.info("Wrote %s", GRAPH_IMAGE_PATH)

    return graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the l2 workflow.")
    parser.add_argument(
        "--ticket",
        action="append",
        default=[],
        metavar="TICKET_ID",
        help="Sample ticket to run; repeat for several (default: all)",
    )
    parser.add_argument("--execute", action="store_true", help="Run the workflow")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Dry run: log agent prompts instead of calling them (implies --execute)",
    )
    parser.add_argument(
        "--output-image",
        action="store_true",
        help="Write the graph diagram to graph.png",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    if args.execute and not args.debug and not get_settings().openai_api_key:
        parser.error("OPENAI_API_KEY must be set (or pass --debug for a dry run)")

    graph = build_graph(output_image=args.output_image)

    if not (args.execute or args.debug):
        return

    tickets = [
        t for t in SAMPLE_TICKETS if not args.ticket or t.ticket_id in args.ticket
    ]
    if not tickets:
        parser.error(f"no sample tickets match {args.ticket}")

    for ticket in tickets:
        result = graph.invoke({"ticket": ticket, "debug": args.debug})
        logger.info(
            "TriageOutput for %s:\n%s",
            ticket.ticket_id,
            result["triage_output"].model_dump_json(indent=2),
        )


if __name__ == "__main__":
    main()
