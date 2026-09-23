"""l2 workflow graph and CLI.

Run from the repo root:
    uv run python -m workflows.practice.l2.graph --execute --input topic="..."
    uv run python -m workflows.practice.l2.graph --debug --input topic="..."   # dry run, no model calls
    uv run python -m workflows.practice.l2.graph --output-image                 # write graph.png
"""

import argparse
import logging
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.nodes.classify_security_risk_node import (
    classify_security_risk_node, requires_security_escalation)
from workflows.practice.l2.nodes.classify_ticket_node import classify_ticket_node
from workflows.practice.l2.nodes.grade_articles_node import (
    grade_articles_node,
    route_after_grading,
)
from workflows.practice.l2.nodes.kb_lookup_node import kb_lookup_node
from workflows.practice.l2.nodes.populate_ticket_details_node import populate_ticket_details_node
from workflows.practice.l2.agents.triage_agent import triage_agent_node
from workflows.practice.l2.nodes.security_handoff_node import security_handoff_node
from workflows.practice.l2.state import InputState, State
from workflows.practice.l2.models import SupportTicket


logger = logging.getLogger(__name__)

GRAPH_IMAGE_PATH = Path(__file__).parent / "graph.png"


def build_graph(output_image: bool = False) -> CompiledStateGraph:
    builder = StateGraph(State, input_schema=InputState)

    # nodes
    builder.add_node("populate_ticket_details", populate_ticket_details_node)
    builder.add_node("classify_security_risk", classify_security_risk_node)
    builder.add_node("classify_ticket", classify_ticket_node)
    builder.add_node("kb_lookup", kb_lookup_node)
    builder.add_node("grade_articles", grade_articles_node)
    builder.add_node("security_handoff", security_handoff_node)
    builder.add_node("triage_agent", triage_agent_node)

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
    # TODO: escalate to kb_search_agent on a miss; route both branches to build_triage_output
    builder.add_conditional_edges(
        "grade_articles", route_after_grading, ["triage_agent", END]
    )

    # final positions
    builder.add_edge("triage_agent", END)
    builder.add_edge("security_handoff", END)

    # compile
    graph = builder.compile()

    if output_image:
        GRAPH_IMAGE_PATH.write_bytes(graph.get_graph(xray=True).draw_mermaid_png())
        logger.info("Wrote %s", GRAPH_IMAGE_PATH)

    return graph


def _key_value(pair: str) -> tuple[str, str]:
    key, sep, value = pair.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {pair!r}")
    return key, value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the l2 workflow.")
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        type=_key_value,
        metavar="KEY=VALUE",
        help="Graph input; repeat for multiple keys",
    )
    parser.add_argument("--execute", action="store_true", help="Run the workflow")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Dry run: log prompts instead of calling models (implies --execute)",
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
    
    sample_tickets = [
        SupportTicket(
            ticket_id="T001",
            employee_id="E001",
            subject="Lost Device",
            description="My device was lost yesterday."
        ),
        SupportTicket(
            ticket_id="T002",
            employee_id="E002",
            subject="Forgot password",
            description="How can I reset my password?"
        )
    ]

    if args.execute or args.debug:
        result = graph.invoke({
            "ticket": sample_tickets[0],
            "debug": args.debug
        })


if __name__ == "__main__":
    main()
