import pytest
from pydantic import ValidationError

from workflows.practice.l1.tools import (
    Customer,
    CustomerNotFoundError,
    PolicyChunk,
    RiskAssessment,
    RiskFactor,
    calculate_risk_tool,
    get_customer_tool,
    search_policy_tool,
)

# --- Customer -------------------------------------------------------------


def test_get_customer_returns_known_customer():
    customer = get_customer_tool("C-10482")
    assert customer.customer_id == "C-10482"
    assert customer.name == "Acme Imports Ltd"
    assert customer.country == "GB"


def test_get_customer_distinguishes_between_customers():
    a = get_customer_tool("C-10482")
    b = get_customer_tool("C-20017")
    assert a.customer_id != b.customer_id
    assert a.name != b.name


def test_get_customer_raises_for_unknown_id():
    with pytest.raises(CustomerNotFoundError, match="C-00000"):
        get_customer_tool("C-00000")


def test_customer_rejects_negative_turnover():
    with pytest.raises(ValidationError):
        Customer(
            customer_id="X",
            name="X",
            country="GB",
            industry="Retail",
            annual_turnover=-1,
            years_in_business=1,
        )


def test_customer_rejects_non_iso2_country():
    with pytest.raises(ValidationError):
        Customer(
            customer_id="X",
            name="X",
            country="GBR",
            industry="Retail",
            annual_turnover=1,
            years_in_business=1,
        )


# --- Policy search --------------------------------------------------------


def test_search_policy_returns_ranked_chunks():
    results = search_policy_tool("wholesale turnover")
    assert results
    assert all(isinstance(r, PolicyChunk) for r in results)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert "wholesale" in results[0].text.lower()


def test_search_policy_respects_top_k():
    assert len(search_policy_tool("business", top_k=2)) <= 2


def test_search_policy_returns_empty_for_no_match():
    assert search_policy_tool("zzzz qqqq") == []


# --- Risk assessment ------------------------------------------------------


def _customer(**overrides) -> Customer:
    base = dict(
        customer_id="C-1",
        name="Test",
        country="GB",
        industry="Retail",
        annual_turnover=100_000,
        years_in_business=10,
    )
    return Customer(**{**base, **overrides})


def test_calculate_risk_low_for_benign_customer():
    result = calculate_risk_tool(_customer())
    assert isinstance(result, RiskAssessment)
    assert result.score == 0
    assert result.rating == "low"
    assert result.factors == []


def test_calculate_risk_flags_high_risk_country():
    result = calculate_risk_tool(_customer(country="NG"))
    assert any(f.code == "HIGH_RISK_COUNTRY" for f in result.factors)
    assert result.score == 2


def test_calculate_risk_flags_wholesale_over_threshold():
    result = calculate_risk_tool(_customer(industry="Wholesale", annual_turnover=4_200_000))
    codes = {f.code for f in result.factors}
    assert "HIGH_VALUE_WHOLESALE" in codes


def test_calculate_risk_does_not_flag_wholesale_under_threshold():
    result = calculate_risk_tool(_customer(industry="Wholesale", annual_turnover=500_000))
    assert not any(f.code == "HIGH_VALUE_WHOLESALE" for f in result.factors)


def test_calculate_risk_flags_new_business():
    result = calculate_risk_tool(_customer(years_in_business=1))
    assert any(f.code == "NEW_BUSINESS" for f in result.factors)


def test_calculate_risk_score_is_sum_of_factor_points():
    result = calculate_risk_tool(
        _customer(country="PK", industry="Wholesale", annual_turnover=2_000_000, years_in_business=1)
    )
    assert result.score == sum(f.points for f in result.factors)
    assert result.rating == "high"


def test_calculate_risk_factors_are_explained():
    result = calculate_risk_tool(_customer(country="NG"))
    factor = result.factors[0]
    assert isinstance(factor, RiskFactor)
    assert factor.description


def test_risk_rating_bands():
    assert RiskAssessment(score=0, factors=[]).rating == "low"
    assert RiskAssessment(score=2, factors=[]).rating == "medium"
    assert RiskAssessment(score=4, factors=[]).rating == "high"
