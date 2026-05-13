from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.messages import HumanMessage

from workflows.hubspot_company_data_population.state import CompanyClassificationOutput


load_dotenv()

SYSTEM_PROMPT_TEMPLATE = """
You are a company sector classification agent.

Use the following skill instructions:

{skill_instructions}

Reference taxonomy:

{taxonomy}
"""

SKILL_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "company-sector-classification-skill"
)


def load_system_prompt() -> str:
    skill_instructions = (SKILL_DIR / "SKILL.md").read_text()
    taxonomy = (SKILL_DIR / "references" / "sector_taxonomy.yaml").read_text()

    return SYSTEM_PROMPT_TEMPLATE.format(
        skill_instructions=skill_instructions,
        taxonomy=taxonomy,
    )


@lru_cache(maxsize=1)
def get_classifier_agent():
    return create_agent(
        model="openai:gpt-5.4-nano",
        system_prompt=load_system_prompt(),
        response_format=ProviderStrategy(CompanyClassificationOutput),
    )


def classify_company_node(state: dict) -> dict:

    company_name = state.get("company_name", "")

    if not company_name:
        return {"classification": None}

    message = HumanMessage(
        content=f"Classify the following company into a sector: {company_name}")

    response = get_classifier_agent().invoke({"messages": [message]})

    return {"classification": response["structured_response"]}
