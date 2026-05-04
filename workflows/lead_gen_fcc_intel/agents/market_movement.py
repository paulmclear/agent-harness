from dotenv import load_dotenv

from tools.perplexity_search_tool import perplexity_search
from workflows.lead_gen_fcc_intel.agents._base import make_analyst_node
from workflows.lead_gen_fcc_intel.data_sources.market_movement_data import (
    fetch_ai_fraud_detection,
    fetch_tech_implementations,
    fetch_transformations,
)

load_dotenv()

SYSTEM_PROMPT = (
    "You are a technology market analyst. Extract ONLY companies and "
    "technologies explicitly mentioned in the data."
)

USER_PROMPT = """You are a market technology analyst for Plenitude Consulting. Today's date is {current_date}. Focus on items from the last two weeks.

## YOUR TASK
Analyze technology adoption, transformation programs, and AI implementations to identify:
1. Companies investing in compliance technology (ONLY if explicitly named)
2. Technology trends in financial crime prevention
3. Modernization initiatives and system upgrades
4. Innovation opportunities

## DATA SOURCES

### Transformation Programmes:
{transformations}

### Technology Implementations:
{tech_implementations}

### AI/Fraud Detection:
{ai_fraud_detection}

## TOOL
Use your Perplexity tool to check any points that need backup and expand on any highly important items.

## OUTPUT REQUIRED
Return a JSON object with:
- tech_adopters: Array of companies implementing new technology (ONLY explicitly named)
- technology_trends: Array of emerging tech trends
- transformation_drivers: What's driving technology change
- innovation_areas: Areas of innovation and opportunity"""


market_movement_node = make_analyst_node(
    name="MarketMovementAgent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    data_sources={
        "transformations": fetch_transformations,
        "tech_implementations": fetch_tech_implementations,
        "ai_fraud_detection": fetch_ai_fraud_detection,
    },
    output_key="market_movement_analysis",
    tools=[perplexity_search],
)
