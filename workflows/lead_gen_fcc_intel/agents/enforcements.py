from dotenv import load_dotenv

from tools.perplexity_search_tool import perplexity_search
from workflows.lead_gen_fcc_intel.agents._base import make_analyst_node
from workflows.lead_gen_fcc_intel.data_sources.reg_intel_data import (
    fetch_aml_fines,
    fetch_regulatory_investigations,
    fetch_sanctions_issues,
)

load_dotenv()

SYSTEM_PROMPT = (
    "You are an enforcement risk analyst. Extract ONLY companies and facts "
    "explicitly mentioned in the data. Never invent details."
)

USER_PROMPT = """You are an enforcement risk analyst for Plenitude Consulting. Today's date is {current_date}. Focus on items from the last two weeks.

## YOUR TASK
Analyze enforcement actions, fines, investigations, and sanctions issues to identify:
1. Companies facing penalties or investigations (ONLY if explicitly named)
2. Types of compliance failures leading to enforcement
3. Enforcement trends and patterns
4. Risk indicators for future enforcement

## DATA SOURCES

### AML Fines:
{aml_fines}

### Regulatory Investigations:
{regulatory_investigations}

### Sanctions Issues:
{sanctions_issues}

## TOOL
Use your Perplexity tool to check any points that need backup and expand on any highly important items.

## OUTPUT REQUIRED
Return a JSON object with:
- enforcement_cases: Array of companies with enforcement actions (ONLY explicitly named)
- failure_patterns: Array of common compliance failure types
- risk_indicators: Array of signals that predict enforcement risk
- sector_exposure: Which sectors are seeing most enforcement"""


enforcement_risk_node = make_analyst_node(
    name="EnforcementRiskAgent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    data_sources={
        "aml_fines": fetch_aml_fines,
        "regulatory_investigations": fetch_regulatory_investigations,
        "sanctions_issues": fetch_sanctions_issues,
    },
    output_key="enforcement_risk_analysis",
    tools=[perplexity_search],
)
