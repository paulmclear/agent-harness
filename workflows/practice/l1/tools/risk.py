"""Risk assessment engine — rule table that yields explainable risk factors."""

from collections.abc import Callable

from workflows.practice.l1.tools.models import Customer, RiskAssessment, RiskFactor

HIGH_RISK_COUNTRIES = frozenset({"NG", "PK"})
HIGH_VALUE_WHOLESALE_THRESHOLD = 1_000_000
NEW_BUSINESS_MAX_YEARS = 3

# Each rule returns a RiskFactor when it applies, otherwise None.
Rule = Callable[[Customer], RiskFactor | None]


def _high_risk_country(c: Customer) -> RiskFactor | None:
    if c.country in HIGH_RISK_COUNTRIES:
        return RiskFactor(
            code="HIGH_RISK_COUNTRY",
            description=f"Customer is located in a high-risk jurisdiction ({c.country}).",
            points=2,
        )
    return None


def _high_value_wholesale(c: Customer) -> RiskFactor | None:
    if c.industry == "Wholesale" and c.annual_turnover > HIGH_VALUE_WHOLESALE_THRESHOLD:
        return RiskFactor(
            code="HIGH_VALUE_WHOLESALE",
            description=(
                f"Wholesale business with annual turnover of {c.annual_turnover:,.0f} "
                f"exceeds the {HIGH_VALUE_WHOLESALE_THRESHOLD:,} threshold."
            ),
            points=2,
        )
    return None


def _new_business(c: Customer) -> RiskFactor | None:
    if c.years_in_business < NEW_BUSINESS_MAX_YEARS:
        return RiskFactor(
            code="NEW_BUSINESS",
            description=(
                f"Only {c.years_in_business} year(s) in business "
                f"(fewer than {NEW_BUSINESS_MAX_YEARS})."
            ),
            points=1,
        )
    return None


RULES: tuple[Rule, ...] = (_high_risk_country, _high_value_wholesale, _new_business)


def calculate_risk_tool(customer: Customer, rules: tuple[Rule, ...] = RULES) -> RiskAssessment:
    factors = [
        f 
        for rule in rules 
        if (f := rule(customer)) is not None
    ]
    return RiskAssessment(score=sum(f.points for f in factors), factors=factors)
