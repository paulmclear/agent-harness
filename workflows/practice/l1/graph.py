import argparse
import os
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from workflows.practice.l1.nodes.build_report_node import build_report_node
from workflows.practice.l1.nodes.calculate_risk_node import calculate_risk_node
from workflows.practice.l1.nodes.get_customer_node import get_customer_node
from workflows.practice.l1.nodes.search_policy_node import search_policy_node
from workflows.practice.l1.nodes.write_report_to_file_node import write_report_to_file_node
from workflows.practice.l1.nodes.risk_assessment_qa_node import risk_assessment_qa_node
from workflows.practice.l1.agents.risk_assessment_agent import risk_assessment_node
from workflows.practice.l1.state import State


load_dotenv()


class WorkflowInput(TypedDict):
    customer_id: str


def build_graph(output_image: bool = False) -> StateGraph[State]:

    workflow_builder = StateGraph(State)

    # nodes
    workflow_builder.add_node("get_customer", get_customer_node)
    workflow_builder.add_node("calculate_risk", calculate_risk_node)
    workflow_builder.add_node("search_policy", search_policy_node)
    workflow_builder.add_node("build_report", build_report_node)
    workflow_builder.add_node("risk_assessment", risk_assessment_node)
    workflow_builder.add_node("risk_assessment_qa", risk_assessment_qa_node)
    workflow_builder.add_node("write_report_to_file", write_report_to_file_node)

    # edges
    workflow_builder.add_edge(START, "get_customer")
    workflow_builder.add_edge("get_customer", "calculate_risk")
    workflow_builder.add_edge("calculate_risk", "search_policy")
    workflow_builder.add_edge("search_policy", "risk_assessment")
    workflow_builder.add_edge("risk_assessment", "risk_assessment_qa")
    workflow_builder.add_edge("risk_assessment_qa", "build_report")
    workflow_builder.add_edge("build_report", "write_report_to_file")
    workflow_builder.add_edge("write_report_to_file", END)

    # compile
    workflow = workflow_builder.compile()

    # output image of the graph
    if output_image:
        with open("workflows/practice/l1/graph.png", "wb") as f:
            f.write(workflow.get_graph(xray=True).draw_mermaid_png())

    return workflow


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-image", action="store_true")
    parser.add_argument("--customer-id", help="ID of the customer to process")
    parser.add_argument("--execute", action="store_true", help="Execute the workflow immediately", )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode", )
    args = parser.parse_args()

    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY must be set in the environment" 

    graph = build_graph(output_image=args.output_image)
    
    if args.debug:
        # check we have customer id for execution
        graph.invoke(input={"customer_id": "C-10482", "debug": args.debug}) # type: ignore
    
    if args.execute:
        # check we have customer id for execution
        if not args.customer_id:
            raise ValueError("Customer ID is required for execution")

        graph.invoke(input={"customer_id": args.customer_id}) # type: ignore
