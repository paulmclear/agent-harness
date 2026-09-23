from workflows.practice.l1.state import State
from workflows.practice.l1.tools import search_policy_tool


def search_policy_node(state: State) -> dict:
    # Query the knowledge base with the customer's profile plus the triggered risk
    # factors, so the report can cite the policies that explain the score.
    customer = state["customer"]
    query = " ".join(
        [customer.industry, customer.country, state["risk"].rating]
        + [f.description for f in state["risk"].factors]
    )
    return {"policy_chunks": search_policy_tool(query)}
