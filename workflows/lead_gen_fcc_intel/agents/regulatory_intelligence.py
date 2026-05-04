from dotenv import load_dotenv

from tools.perplexity_search_tool import perplexity_search
from workflows.lead_gen_fcc_intel.agents._base import make_analyst_node
from workflows.lead_gen_fcc_intel.data_sources.reg_intel_data import (
    fetch_boe_news,
    fetch_fca_news,
    fetch_pra_publications,
)

load_dotenv()

SYSTEM_PROMPT = (
    "You are a regulatory intelligence analyst. Extract ONLY factual "
    "information explicitly present in the data. Never fabricate company "
    "names or details."
)

USER_PROMPT = """You are a regulatory intelligence analyst for Plenitude Consulting. Today's date is {current_date}. Focus on material for the last 2 weeks.

## YOUR TASK
Analyze regulatory news, FCA updates, PRA publications, and BOE announcements to identify:
1. New regulatory requirements or policy changes
2. Regulatory themes and enforcement priorities
3. Companies mentioned in regulatory context
4. Compliance pressure points affecting the industry

## DATA SOURCES

### FCA News:
{fca_news}

### PRA Publications:
{pra_publications}

### Bank of England News:
{boe_news}

## TOOL
Use your Perplexity tool to check any points that need backup and expand on any highly important items.

## OUTPUT REQUIRED
Return a JSON object with:
- regulatory_themes: Array of emerging regulatory themes
- affected_companies: Array of companies mentioned (ONLY if explicitly named)
- new_requirements: Array of new compliance requirements identified
- pressure_points: Areas where firms are struggling with compliance"""


regulatory_intelligence_node = make_analyst_node(
    name="RegulatoryIntelligenceAgent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt=USER_PROMPT,
    data_sources={
        "fca_news": fetch_fca_news,
        "pra_publications": fetch_pra_publications,
        "boe_news": fetch_boe_news,
    },
    output_key="regulatory_intelligence_analysis",
    tools=[perplexity_search],
)
