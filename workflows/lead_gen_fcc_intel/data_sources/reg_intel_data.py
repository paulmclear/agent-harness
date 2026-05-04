"""Data fetchers for the lead-gen FCC intelligence workflow.

Mirrors the n8n spec at
specs/lead-gen-fcc-intelligence/{workflow.yaml, agents/}: each Perplexity
search uses sonar-pro with a system+user prompt and a one-month recency
window; each regulatory source is a raw HTTP/RSS GET whose body is handed
to the analyst LLM verbatim.
"""

from __future__ import annotations

import urllib.error
import urllib.request

from workflows.lead_gen_fcc_intel.data_sources._perplexity import (
    perplexity_chat,
    researcher_system_prompt,
)

_USER_AGENT = "Mozilla/5.0 (compatible; aura-fcc-intel/1.0)"
_HTTP_TIMEOUT = 30

_FCA_URLS = (
    "https://www.fca.org.uk/news/search-results"
    "?category=news%20stories%2Cpress%20releases%2Cstatements%2Cspeeches%2Cblogs"
    "&sort_by=dmetaZ&start=1",
    "https://www.fca.org.uk/news/search-results"
    "?category=news%20stories%2Cpress%20releases%2Cstatements%2Cspeeches%2Cblogs"
    "&sort_by=dmetaZ&start=2",
    "https://www.fca.org.uk/publications/search-results"
    "?p_search_term=&category=policy%20and%20guidance-dear%20ceo%20letters"
    "&sort_by=dmetaZ&start=1",
)
_PRA_RSS = "https://www.bankofengland.co.uk/rss/prudential-regulation-publications"
_BOE_RSS = "https://www.bankofengland.co.uk/rss/news"


def _fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"[fetch error for {url}: {exc}]"


def fetch_fca_news() -> str:
    return "\n\n---\n\n".join(_fetch_url(url) for url in _FCA_URLS)


def fetch_pra_publications() -> str:
    return _fetch_url(_PRA_RSS)


def fetch_boe_news() -> str:
    return _fetch_url(_BOE_RSS)


def fetch_aml_fines() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK banks, financial institutions, or "
        "companies that have been fined for money laundering or AML breaches "
        "in 2024-2025. ONLY provide specific company names mentioned in "
        "regulatory announcements or news and provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_regulatory_investigations() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of financial services companies in UK or "
        "Europe currently under regulatory investigation or enforcement "
        "action for compliance failures. ONLY provide specific company names "
        "from official regulatory sources or news reports and provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)


def fetch_sanctions_issues() -> str:
    user_prompt = (
        "List the ACTUAL NAMES of UK financial services companies "
        "experiencing sanctions screening challenges, high false positive "
        "rates, or transaction monitoring alert issues. ONLY provide "
        "specific company names mentioned in regulatory reports or industry "
        "news and provide details."
    )
    return perplexity_chat(researcher_system_prompt(), user_prompt)
