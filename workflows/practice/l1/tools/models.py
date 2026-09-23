from typing import Literal

from pydantic import BaseModel, Field, computed_field

RiskRating = Literal["low", "medium", "high"]


class Customer(BaseModel):
    customer_id: str
    name: str
    country: str = Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2 code")
    industry: str
    annual_turnover: float = Field(ge=0)
    years_in_business: int = Field(ge=0)


class PolicyChunk(BaseModel):
    id: str
    title: str
    text: str
    score: float = 0.0


class RiskFactor(BaseModel):
    code: str
    description: str
    points: int = Field(ge=0)


class RiskAssessment(BaseModel):
    score: int = Field(ge=0)
    factors: list[RiskFactor]

    @computed_field
    @property
    def rating(self) -> RiskRating:
        if self.score >= 4:
            return "high"
        if self.score >= 2:
            return "medium"
        return "low"
