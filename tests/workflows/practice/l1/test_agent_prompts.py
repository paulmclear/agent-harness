import os

import pytest

from workflows.practice.l1.agents._base import get_user_prompt
from workflows.practice.l1.tools import (
    calculate_risk_tool,
    get_customer_tool,
    search_policy_tool,
)


@pytest.fixture
def user_prompt_template():
    # Importing the agent module constructs the model client, which needs a key.
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    from workflows.practice.l1.agents.risk_assessment_agent import USER_PROMPT_TEMPLATE

    return USER_PROMPT_TEMPLATE


def test_risk_assessment_user_prompt_formats_with_real_state(user_prompt_template):
    customer = get_customer_tool("C-30355")
    risk = calculate_risk_tool(customer)
    state = {
        "customer_id": customer.customer_id,
        "customer": customer,
        "risk": risk,
        "policy_chunks": search_policy_tool("wholesale high-risk"),
    }
    prompt = get_user_prompt(user_prompt_template, state)
    assert "Lagos Trade Partners" in prompt
    assert "HIGH_RISK_COUNTRY" in prompt
    assert "POL-12" in prompt
