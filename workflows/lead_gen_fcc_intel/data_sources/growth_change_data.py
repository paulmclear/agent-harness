"""Layer-1 Perplexity collectors feeding `agent_growth_change`.

Mirrors specs/lead-gen-fcc-intelligence/agents/search_*.yaml for:
appointments, mergers_acquisitions, international_expansion, compliance_costs.
"""

from __future__ import annotations

from workflows.lead_gen_fcc_intel.data_sources._perplexity import (
    perplexity_chat,
    researcher_system_prompt,
)


def fetch_appointments() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK financial services companies that have "
        "recently appointed new heads of financial crime, MLROs, or chief "
        "compliance officers. Include the company name and the person's name "
        "if available. ONLY from news or press releases and provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_mergers_acquisitions() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK financial services firms involved in "
        "recent mergers, acquisitions, or integration projects requiring "
        "compliance harmonization. Include both acquirer and target company "
        "names. ONLY from official announcements or news and provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_international_expansion() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK banks or insurance companies planning "
        "international expansion or entering new markets requiring "
        "regulatory approvals. Include specific company names and target "
        "countries. ONLY from press releases or regulatory filings and "
        "provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_compliance_costs() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK banks or financial institutions that "
        "have publicly reported rising financial crime compliance costs or "
        "increased regulatory pressure in 2024-2025. ONLY provide specific "
        "company names from earnings reports or regulatory disclosures and "
        "provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)
