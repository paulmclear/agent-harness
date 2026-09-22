from workflows.practice.l1.state import State
from workflows.practice.l1.tools import get_customer_tool


def get_customer_node(state: State) -> dict:
    customer = get_customer_tool(customer_id=state["customer_id"])
    return {"customer": customer}
