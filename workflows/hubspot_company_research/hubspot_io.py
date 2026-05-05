"""HubSpot integration nodes for the Company Research workflow.

Mirrors the `get_company_data` and `update_hubspot_record` integration nodes
in specs/hubspot-company-research/workflow.yaml. Uses the shared
HubSpotService so the same OAuth token configuration applies.
"""

from __future__ import annotations

from services.hubspot_client import HubSpotService
from workflows.hubspot_company_research.state import AgentState

# Properties needed by prepare_research_context. Pulling a focused list keeps
# the response small; HubSpot returns whatever is requested.
_COMPANY_PROPERTIES = [
    "name",
    "domain",
    "industry",
    "numberofemployees",
    "annualrevenue",
    "city",
    "country",
    "intelligence_report",
    "intelligence_report_status",
]

_REPORT_PROPERTY = "intelligence_report"
_STATUS_PROPERTY = "intelligence_report_status"
_STATUS_DONE = "Updated"


def get_company_data_node(state: AgentState) -> AgentState:
    company_id = state.get("company_id")
    if not company_id:
        raise ValueError("get_company_data_node: state['company_id'] is required")

    service = HubSpotService()
    company = service.get_company(company_id, properties=_COMPANY_PROPERTIES)
    state["company_properties"] = company.get("properties") or {}
    return state


def update_hubspot_record_node(state: AgentState) -> AgentState:
    company_id = state.get("company_id")
    report_html = state.get("report_html")
    if not company_id:
        raise ValueError("update_hubspot_record_node: state['company_id'] is required")
    if not report_html:
        raise ValueError("update_hubspot_record_node: state['report_html'] is empty")

    service = HubSpotService()
    service.update_company(
        company_id,
        properties={
            _REPORT_PROPERTY: report_html,
            _STATUS_PROPERTY: _STATUS_DONE,
        },
    )
    state["hubspot_update_status"] = _STATUS_DONE
    return state
