from workflows.practice.l1.state import State
from workflows.practice.l1.tools import calculate_risk_tool


def calculate_risk_node(state: State) -> dict:
    return {"risk": calculate_risk_tool(state["customer"])}
