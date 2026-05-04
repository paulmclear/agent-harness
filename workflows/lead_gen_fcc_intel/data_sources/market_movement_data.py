"""Layer-1 Perplexity collectors feeding `agent_market_movement`.

Mirrors specs/lead-gen-fcc-intelligence/agents/search_*.yaml for:
transformations, tech_implementations, ai_fraud_detection.
"""

from __future__ import annotations

from workflows.lead_gen_fcc_intel.data_sources._perplexity import (
    perplexity_chat,
    researcher_system_prompt,
)


def fetch_transformations() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK banks, insurance companies, or asset "
        "managers that have announced financial crime transformation "
        "programmes, compliance upgrades, or AML system replacements. ONLY "
        "provide specific company names from press releases or news and "
        "provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_tech_implementations() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK banks or financial institutions that "
        "have announced new transaction monitoring systems, AML screening "
        "technology implementations, or financial crime tech upgrades. ONLY "
        "provide specific company names from announcements or news and "
        "provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_ai_fraud_detection() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK fintech companies, challenger banks, "
        "or financial institutions implementing AI fraud detection or "
        "machine learning for financial crime prevention. ONLY provide "
        "specific company names from press releases or news articles and "
        "provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)
