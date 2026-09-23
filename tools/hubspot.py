# tools.py

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from services.hubspot_client import HubSpotService


hubspot = HubSpotService()


class SearchHubSpotContactInput(BaseModel):
    email: str = Field(
        description="The email address of the HubSpot contact to search for."
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of contacts to return.",
    )


@tool(args_schema=SearchHubSpotContactInput)
def search_hubspot_contact_by_email(email: str, limit: int = 5) -> list[dict]:
    """
    Search HubSpot CRM contacts by email address.

    Use this when the user asks about a specific person, customer, prospect,
    or contact and provides their email address.
    """
    return hubspot.search_contacts_by_email(email=email, limit=limit)


class SearchHubSpotCompany(BaseModel):
    company_name: str = Field(
        description="The name of the HubSpot company to search for."
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of companies to return.",
    )


@tool(args_schema=SearchHubSpotCompany)
def search_hubspot_company_by_name(company_name: str, limit: int = 5) -> list[dict]:
    """
    Search HubSpot CRM companies by name.

    Use this when the user asks about a specific company and provides their name.
    """
    return hubspot.search_company(company_name=company_name, limit=limit)
