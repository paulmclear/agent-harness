# hubspot_client.py

import os
from typing import Any

from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.companies import (
    ApiException as CompaniesApiException,
    SimplePublicObjectInput,
    PublicObjectSearchRequest,
    ApiException
)

load_dotenv()


class HubSpotService:
    def __init__(self) -> None:
        access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")

        if not access_token:
            raise ValueError("HUBSPOT_ACCESS_TOKEN is not set")

        self.client = HubSpot(access_token=access_token)

    def search_contacts_by_email(
        self,
        email: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search HubSpot contacts by email address.
        """

        request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                }
            ],
            properties=[
                "email",
                "firstname",
                "lastname",
                "company",
                "jobtitle",
                "phone",
                "lifecyclestage",
            ],
            limit=limit,
        )

        try:
            response = self.client.crm.contacts.search_api.do_search(
                public_object_search_request=request
            )
        except ApiException as exc:
            raise RuntimeError(f"HubSpot contacts search failed: {exc}") from exc

        return [
            {
                "id": contact.id,
                "properties": contact.properties,
                "created_at": str(contact.created_at),
                "updated_at": str(contact.updated_at),
            }
            for contact in response.results
        ]

    def get_company(
        self,
        company_id: str,
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch a HubSpot Company record by id."""
        try:
            company = self.client.crm.companies.basic_api.get_by_id(
                company_id=company_id,
                properties=properties,
            )
        except CompaniesApiException as exc:
            raise RuntimeError(f"HubSpot company fetch failed: {exc}") from exc

        return {
            "id": company.id,
            "properties": company.properties,
            "created_at": str(company.created_at),
            "updated_at": str(company.updated_at),
        }

    def update_company(
        self,
        company_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Update properties on a HubSpot Company record."""
        try:
            company = self.client.crm.companies.basic_api.update(
                company_id=company_id,
                simple_public_object_input=SimplePublicObjectInput(
                    properties=properties
                ),
            )
        except CompaniesApiException as exc:
            raise RuntimeError(f"HubSpot company update failed: {exc}") from exc

        return {
            "id": company.id,
            "properties": company.properties,
            "updated_at": str(company.updated_at),
        }

    def list_companies(
        self,
        limit: int = 10,
        properties: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List HubSpot Company records, auto-paginating when `limit` exceeds 100.

        HubSpot's CRM v3 API caps each page at 100 and uses cursor-based pagination
        via `paging.next.after`. We page until we have `limit` results or run out.
        """
        page_size_cap = 100
        results: list[dict[str, Any]] = []
        after: str | None = None

        while len(results) < limit:
            page_limit = min(page_size_cap, limit - len(results))
            try:
                response = self.client.crm.companies.basic_api.get_page(
                    limit=page_limit,
                    after=after,
                    properties=properties,
                )
            except CompaniesApiException as exc:
                raise RuntimeError(f"HubSpot company list failed: {exc}") from exc

            results.extend(
                {
                    "id": company.id,
                    "properties": company.properties,
                    "created_at": str(company.created_at),
                    "updated_at": str(company.updated_at),
                }
                for company in response.results
            )

            next_page = getattr(response.paging, "next", None) if response.paging else None
            after = next_page.after if next_page else None
            if after is None:
                break

        return results

    def search_company(
        self,
        company_name: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search HubSpot Company records by name."""
        request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "propertyName": "name",
                            "operator": "EQ",
                            "value": company_name,
                        }
                    ]
                }
            ],
            properties=[
                "name",
                "domain",
                "industry",
                "phone",
                "website",
            ],
            limit=limit,
        )

        try:
            response = self.client.crm.companies.search_api.do_search(
                public_object_search_request=request
            )
        except CompaniesApiException as exc:
            raise RuntimeError(f"HubSpot company search failed: {exc}") from exc

        return [
            {
                "id": company.id,
                "properties": company.properties,
                "created_at": str(company.created_at),
                "updated_at": str(company.updated_at),
            }
            for company in response.results
        ]
