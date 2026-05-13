import pprint

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from services.hubspot_client import HubSpotService

from workflows.hubspot_company_data_population.nodes.seen_list_node import check_seen_list_router, add_to_seen_list_node
from workflows.hubspot_company_data_population.state import AgentState
from workflows.hubspot_company_data_population.nodes.classifier_agent_node import classify_company_node
from workflows.hubspot_company_data_population.nodes.web_search_node import (
    needs_web_search_router,
    web_search_node,
)
from workflows.hubspot_company_data_population.repo import HubSpotCompanyRepository
from workflows.hubspot_company_data_population.to_csv import output_to_csv


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    # add nodes
    graph.add_node("classify_company_node", classify_company_node)
    graph.add_node("web_search_node", web_search_node)
    graph.add_node("add_to_seen_list", add_to_seen_list_node)

    # add edges
    graph.add_conditional_edges(START, check_seen_list_router, {
        True: END,
        False: "classify_company_node"
    })
    graph.add_conditional_edges("classify_company_node", needs_web_search_router, {
        "web_search": "web_search_node",
        "done": "add_to_seen_list",
    })
    graph.add_edge("web_search_node", "add_to_seen_list")
    graph.add_edge("add_to_seen_list", END)

    return graph.compile()


if __name__ == "__main__":
    graph = build_graph()

    hubspot = HubSpotService()
    companies = hubspot.list_companies(limit=120)

    repo = HubSpotCompanyRepository(db_path="data/hubspot_companies.db")

    for company in companies:

        company_name = company['properties']['name']
        hubspot_id = company['id']

        initial_state = {
            "company_name": company_name
        }

        print(f"Processing company: {company_name}")

        final_state = graph.invoke(initial_state)

        if final_state.get("classification"):
            repo.add_company(
                name=company_name, 
                hubspot_id=hubspot_id, 
                data=final_state['classification'].model_dump()
            )

    # output to csv
    output_to_csv(repo, "normalised_hubspot_companies.csv")