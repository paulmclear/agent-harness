"""dev_loop workflow graph and CLI.

Run from the repo root:
    uv run python -m workflows.dev_loop.graph --execute --input KEY=VALUE
    uv run python -m workflows.dev_loop.graph --debug --input KEY=VALUE   # dry run, no model calls
    uv run python -m workflows.dev_loop.graph --output-image              # write graph.png
"""

import argparse
import logging
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from workflows.dev_loop.config import get_settings
from workflows.dev_loop.state import InputState, State

logger = logging.getLogger(__name__)

GRAPH_IMAGE_PATH = Path(__file__).parent / "graph.png"


def build_graph(output_image: bool = False) -> CompiledStateGraph:
    builder = StateGraph(State, input_schema=InputState)

    # nodes

    # edges
    builder.add_edge(START, END)

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
    parser = argparse.ArgumentParser(description="Run the dev_loop workflow.")
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

    if args.execute or args.debug:
        result = graph.invoke({**dict(args.input), "debug": args.debug})
        logger.info("Finished: %s", result)


if __name__ == "__main__":
    main()
