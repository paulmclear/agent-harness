from typing import Literal, TypedDict

from pydantic import BaseModel, Field


ClassificationFlag = Literal[
    "ambiguous_company_name",
    "insufficient_public_information",
    "multiple_business_lines",
    "out_of_taxonomy",
    "jurisdiction_unclear",
]


class CompanyClassificationOutput(BaseModel):
    rationale: str = Field(description="A brief explanation of the classification.")
    confidence: float = Field(
        ge=0,
        le=1,
        description="A confidence score between 0 and 1 indicating the confidence of the classification.",
    )
    sector: str = Field(description="The sector the company belongs to.")
    sub_sector: str = Field(description="The sub-sector the company belongs to.")
    flags: list[ClassificationFlag] = Field(
        default_factory=list,
        description="Any relevant classification flags from the controlled vocabulary.",
    )
    suggested_sector: str | None = Field(
        default=None,
        description="If the company doesn't fit well into the taxonomy, suggest a more appropriate sector.",
    )
    suggested_sub_sector: str | None = Field(
        default=None,
        description="If the company doesn't fit well into the taxonomy, suggest a more appropriate sub-sector.",
    )


class AgentState(TypedDict):

    # input data
    company_name: str

    # control state
    is_seen: bool = False
    seen_list_enabled: bool = False

    # output data
    classification: CompanyClassificationOutput
