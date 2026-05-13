from pathlib import Path

from workflows.hubspot_company_data_population.state import AgentState


SEEN_LIST_PATH = Path(
    Path.cwd() / 
    "workflows" /
    "hubspot_company_data_population" /
    "seen_companies.txt"
)


def check_seen_list_router(state: AgentState):
    """
    Check if the company has already been processed by this workflow.

    This is a simple example of how to maintain state across workflow runs.
    In a real implementation, you would likely want to persist this data in a database
    or other storage solution.
    """

    company_name = state['company_name']

    if not SEEN_LIST_PATH.exists():
        SEEN_LIST_PATH.touch()
        return {'is_seen': False}

    with SEEN_LIST_PATH.open("r") as f:
        seen_list = [line.strip() for line in f.readlines()]

    if company_name in seen_list:
        is_seen = True
        print(f"Company '{company_name}' has already been processed.")
    else:
        is_seen = False
        print(f"Company '{company_name}' is new and will be processed.")

    return is_seen


def add_to_seen_list_node(state: AgentState):
    """
    Add the company to the seen list.
    """

    company_name = state['company_name']

    with SEEN_LIST_PATH.open("a") as f:
        f.write(f"{company_name}\n")

    return state
