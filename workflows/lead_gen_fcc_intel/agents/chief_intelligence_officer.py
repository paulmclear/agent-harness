import datetime as dt

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from workflows.lead_gen_fcc_intel.state import AgentState

load_dotenv()


SYSTEM_PROMPT = """
You are a Chief Intelligence Officer. Write a professional intelligence report in plain text. Use ONLY real company names from the data provided.
""".strip()


USER_PROMPT = """
## YOUR ROLE

You are the Chief Intelligence Officer for Plenitude Consulting. Today's date is {current_date}.

## YOUR TASK

Provide a concise, current intelligence briefing in plain text using the format and constraints below.

### MARKET OVERVIEW
- Summarize recent trends and research with key dates, names, and specific insights. Normalize field names.
- Extract key themes from analyst data inputs: regulation, enforcement, risk, cyber, AI, and notable market events.
- Highlight technology adoption trends, especially emerging AI threats.
- Note recent enforcement activity trends.
- Predict growth areas and scaling opportunities.
- If any topic area is missing or malformed, clearly state: "No data available for [TOPIC]".

### COMPANY-SPECIFIC LEADS
For each unique company from analyst inputs:
- Merge all signals and insights into a single, consolidated entry. Normalize company field names (e.g., "company", "firm").
- For each company, always preserve this structure, even if data is missing (provide 'No recent signals.' or 'No available summary' where needed):

[COMPANY NAME IN CAPS]
- Summary: [detailed summary or "No available summary"]
- Signals:
  - [type] – [description] (Date: [YYYY-MM-DD])
  - If no signals, write "No recent signals."
- Why Contact: [reason from signals or "No urgent reason identified."]
- Our Pitch: [solution or "No tailored pitch available."]
- Urgency: [High/Medium/Low]
- Action: [next step or "Monitor for developments."]


- If a company appears in multiple sources, combine data under one heading.
- List all companies found in inputs, even with no recent signals.
- Order companies alphabetically.

### IMMEDIATE PRIORITIES
- Identify up to 5 top companies for contact this week based on urgency, signal strength, and business relevance. If fewer than 5, list all that qualify.
- For each:
  - Company: [COMPANY NAME]
    - Timing: [window or "Timing not specified."]
    - Talking Points:
      - [point 1]
      - [point 2]

## FORMATTING
- Do not use markdown (no **, >, or ---).
- All section headers and company names in CAPS.
- Leave blank lines between sections and company entries.
- Use hyphens for bullets.
- No tables.

## RULES
- Only include items from the last 1–2 weeks. Ignore entries older than 4 weeks.

## ANALYST INPUTS:

REGULATORY INTELLIGENCE:
{regulatory_intelligence_input}

ENFORCEMENT & RISK INTELLIGENCE:
{enforcement_risk_input}

MARKET MOVEMENT INTELLIGENCE:
{market_movement_input}

GROWTH & CHANGE INTELLIGENCE:
{growth_change_input}

## Output Format
Follow this plaintext briefing schema:

SCHEMA:

MARKET OVERVIEW
- [Bulleted summary of market trends, key themes, dates, etc.]

COMPANY-SPECIFIC LEADS
[COMPANY 1 NAME IN CAPS]
- Summary: ...
- Signals:
  - [type] – [description] (Date: YYYY-MM-DD)
- Why Contact: ...
- Our Pitch: ...
- Urgency: [High/Medium/Low]
- Action: ...

[COMPANY 2 NAME IN CAPS]
- ...

IMMEDIATE PRIORITIES
- Company: [COMPANY NAME]
  - Timing: ...
  - Talking Points:
    - [point 1]
    - [point 2]

(Repeat for up to 5 companies)

Notes:
- Output only fields listed above.
- Use "No data available for [TOPIC]" or "No recent signals." where data is missing.
""".strip()

agent = create_agent(
    name="ChiefIntelligenceOfficerAgent",
    system_prompt=SYSTEM_PROMPT,
    model="openai:gpt-5.4",
)


def chief_intelligence_officer_node(state: AgentState):
    # format the user prompt with the relevant sections of state
    formatted_user_prompt = USER_PROMPT.format(
        current_date=dt.datetime.now().strftime("%Y-%m-%d"),
        regulatory_intelligence_input=state.get(
            "regulatory_intelligence_analysis",
            "No data available for regulatory intelligence.",
        ),
        enforcement_risk_input=state.get(
            "enforcement_risk_analysis",
            "No data available for enforcement and risk intelligence.",
        ),
        market_movement_input=state.get(
            "market_movement_analysis",
            "No data available for market movement intelligence.",
        ),
        growth_change_input=state.get(
            "growth_change_analysis",
            "No data available for growth and change intelligence.",
        ),
    )

    # run the agent with the formatted prompt
    output = agent.invoke({"messages": [HumanMessage(content=formatted_user_prompt)]})

    # store the final assistant message text as the report
    state["chief_intelligence_report"] = output["messages"][-1].content

    return state
