from dotenv import load_dotenv

from tools.perplexity_search_tool import perplexity_search
from workflows.lead_gen_fcc_intel.agents._base import make_analyst_node
from workflows.lead_gen_fcc_intel.data_sources.growth_change_data import (
    fetch_appointments,
    fetch_compliance_costs,
    fetch_international_expansion,
    fetch_mergers_acquisitions,
)

load_dotenv()

SYSTEM_PROMPT = (
    "You are a strategic growth analyst. Extract ONLY companies and "
    "individuals explicitly mentioned in the data."
)

USER_PROMPT = """You are a strategic growth analyst for Plenitude Consulting. Today's date is {current_date}. Focus on items from the last two weeks.

## YOUR TASK
Analyze leadership changes, M&A activity, expansion plans, and cost pressures to identify:
1. Companies with new leadership or strategic changes (ONLY if explicitly named)
2. M&A activity creating integration needs
3. Growth strategies requiring compliance support
4. Cost pressure creating efficiency needs

## DATA SOURCES

### Leadership Appointments:
{appointments}

### Mergers & Acquisitions:
{mergers_acquisitions}

### International Expansion:
{international_expansion}

### Compliance Costs:
{compliance_costs}

## TOOL
Use your Perplexity tool to check any points that need backup and expand on any highly important items.

## OUTPUT REQUIRED
Return a JSON object with:
- leadership_changes: Array of companies with new compliance leaders (ONLY explicitly named)
- ma_activity: Array of M&A deals requiring compliance integration
- expansion_plans: Companies expanding to new markets
- cost_pressures: Companies citing compliance cost issues"""


growth_change_node = make_analyst_node(
    name="GrowthChangeAgent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    data_sources={
        "appointments": fetch_appointments,
        "mergers_acquisitions": fetch_mergers_acquisitions,
        "international_expansion": fetch_international_expansion,
        "compliance_costs": fetch_compliance_costs,
    },
    output_key="growth_change_analysis",
    tools=[perplexity_search],
)
