"""Pure-data transform nodes for the HubSpot Company Research workflow.

Each function is a LangGraph node taking AgentState and returning a partial
AgentState patch. Mirrors specs/hubspot-company-research/transforms/*.yaml.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any

from workflows.hubspot_company_research.state import AgentState

# Fixed batch ordering used by extract_deduplicate_citations and detect_data_gaps.
_BATCH_ORDER = (
    ("corporate_intelligence", "corporate_intelligence_raw"),
    ("opportunity_signals", "opportunity_signals_raw"),
    ("internal_analysis", "internal_analysis_raw"),
    ("relationship_intelligence", "relationship_intelligence_raw"),
    ("commercial_intelligence", "commercial_intelligence_raw"),
    ("strategic_assessment", "strategic_assessment_raw"),
)


# ── prepare_research_context ─────────────────────────────────────────────


def _coerce_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def _coerce_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def prepare_research_context_node(state: AgentState) -> AgentState:
    props = state.get("company_properties") or {}
    employees = _coerce_int(props.get("numberofemployees"))
    revenue = _coerce_float(props.get("annualrevenue"))
    city = (props.get("city") or "").strip()
    country = (props.get("country") or "").strip()

    if employees > 1000:
        company_type = "large"
    elif employees > 250:
        company_type = "medium"
    else:
        company_type = "small"

    state["company_name"] = props.get("name") or "Unknown"
    state["domain"] = props.get("domain") or ""
    state["industry"] = props.get("industry") or ""
    state["employees"] = employees
    state["revenue"] = revenue
    state["location"] = ", ".join(part for part in (city, country) if part)
    state["company_type"] = company_type
    state["is_public"] = revenue > 100_000_000
    return state


# ── extract_deduplicate_citations ────────────────────────────────────────


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _parse_batch_payload(raw: str | None) -> dict:
    """Parse a Perplexity batch's text output into a dict.

    Tolerates either raw JSON or a markdown-fenced ```json ... ``` block.
    Returns {} on failure so downstream gap detection can still run.
    """
    if not raw:
        return {}
    text = raw.strip()
    if text.startswith("{") or text.startswith("["):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            pass
    match = _JSON_FENCE.search(text)
    if match:
        try:
            parsed = json.loads(match.group(1))
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            pass
    return {"raw": text}


def extract_deduplicate_citations_node(state: AgentState) -> AgentState:
    research_data: dict[str, dict] = {}
    citation_registry: dict[str, dict] = {}  # url → {id, url, title, publishedDate}
    next_id = 1

    for batch_name, state_key in _BATCH_ORDER:
        parsed = _parse_batch_payload(state.get(state_key))
        research_data[batch_name] = parsed
        sources = parsed.get("sources") if isinstance(parsed, dict) else None
        if not isinstance(sources, list):
            continue
        for src in sources:
            if not isinstance(src, dict):
                continue
            url = src.get("url")
            if not url or url in citation_registry:
                continue
            citation_registry[url] = {
                "id": next_id,
                "url": url,
                "title": src.get("title") or "Source",
                "publishedDate": src.get("publishedDate"),
            }
            next_id += 1

    citations = list(citation_registry.values())
    state["research_data"] = research_data
    state["citations"] = citations
    state["total_citations"] = len(citations)
    state["research_date"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return state


# ── detect_data_gaps ─────────────────────────────────────────────────────


_EXPECTED_BY_SIZE = {
    "large": [
        ("corporate_intelligence.employee_count", True),
        ("corporate_intelligence.annual_revenue", True),
    ],
    "medium": [
        ("corporate_intelligence.employee_count", True),
    ],
    "small": [
        ("corporate_intelligence.recent_acquisitions", True),
    ],
}


def _resolve_path(data: dict, path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def detect_data_gaps_node(state: AgentState) -> AgentState:
    research_data = state.get("research_data") or {}
    company_type = state.get("company_type") or "medium"
    expected = _EXPECTED_BY_SIZE.get(company_type, _EXPECTED_BY_SIZE["medium"])

    gaps: list[dict] = []
    for path, critical in expected:
        value = _resolve_path(research_data, path)
        is_missing = (
            value is None
            or value == ""
            or value == 0
            or (isinstance(value, list) and len(value) == 0)
        )
        if is_missing:
            field_name = path.split(".")[-1]
            gaps.append({"field": field_name, "source": path, "critical": critical})

    critical_gaps = sum(1 for g in gaps if g["critical"])
    state["gaps"] = gaps
    state["total_gaps"] = len(gaps)
    state["critical_gaps"] = critical_gaps
    state["has_gaps"] = len(gaps) > 0
    return state


# ── merge_gap_data ───────────────────────────────────────────────────────


def merge_gap_data_node(state: AgentState) -> AgentState:
    """Merge ai_agent_fill_gaps output back into research_data.

    The gap-filler returns a JSON blob with shape {"filled_data": {...}}.
    """
    filled_raw = state.get("filled_data")
    if isinstance(filled_raw, str):
        try:
            parsed = json.loads(filled_raw)
        except json.JSONDecodeError:
            match = _JSON_FENCE.search(filled_raw)
            parsed = json.loads(match.group(1)) if match else {}
    elif isinstance(filled_raw, dict):
        parsed = filled_raw
    else:
        parsed = {}

    filled_data = parsed.get("filled_data") if isinstance(parsed, dict) else None
    if not isinstance(filled_data, dict):
        filled_data = {}

    research_data = dict(state.get("research_data") or {})
    research_data["gap_filled_data"] = filled_data
    state["research_data"] = research_data
    state["filled_data"] = filled_data
    state["gaps_filled"] = len(filled_data)
    return state


def no_gaps_pass_through_node(state: AgentState) -> AgentState:
    """Identity node used when has_gaps is False (parallels no_gaps_pass_through.yaml)."""
    state["gaps_filled"] = 0
    return state


# ── convert_markdown_to_html ─────────────────────────────────────────────


_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$", re.MULTILINE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[(.+?)\]\((https?://[^\s)]+)\)")
_BULLET_RE = re.compile(r"^- +(.*)$", re.MULTILINE)
_LI_BLOCK_RE = re.compile(r"<li>.*?</li>(?:\n<li>.*?</li>)*", re.DOTALL)
_TABLE_RE = re.compile(
    r"((?:^\|.*\|\s*\n)+)(^\|[\s:-]+\|\s*\n)((?:^\|.*\|\s*\n?)+)",
    re.MULTILINE,
)


def _render_table(match: re.Match[str]) -> str:
    header_line = match.group(1).strip().splitlines()[0]
    body_lines = [ln for ln in match.group(3).strip().splitlines() if ln.strip()]
    header_cells = [c.strip() for c in header_line.strip().strip("|").split("|")]
    rows = [
        [c.strip() for c in ln.strip().strip("|").split("|")]
        for ln in body_lines
    ]
    head = "".join(
        f'<th style="border:1px solid #ddd;padding:6px">{c}</th>' for c in header_cells
    )
    body = "".join(
        "<tr>" + "".join(
            f'<td style="border:1px solid #ddd;padding:6px">{c}</td>' for c in row
        ) + "</tr>"
        for row in rows
    )
    return (
        f'<table style="border-collapse:collapse;border:1px solid #ddd">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def _markdown_to_html(markdown: str) -> str:
    text = markdown
    text = _TABLE_RE.sub(_render_table, text)

    def heading_repl(m: re.Match[str]) -> str:
        level = len(m.group(1))
        return f"<h{level}>{m.group(2).strip()}</h{level}>"

    text = _HEADING_RE.sub(heading_repl, text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _LINK_RE.sub(r'<a href="\2" target="_blank">\1</a>', text)
    text = _BULLET_RE.sub(r"<li>\1</li>", text)
    text = _LI_BLOCK_RE.sub(lambda m: f"<ul>{m.group(0)}</ul>", text)

    paragraphs = re.split(r"\n\s*\n", text)
    rendered: list[str] = []
    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            continue
        if re.match(r"^<(h[1-6]|ul|table)", stripped):
            rendered.append(stripped)
        else:
            rendered.append("<p>" + stripped.replace("\n", "<br>") + "</p>")
    return "\n".join(rendered)


def convert_markdown_to_html_node(state: AgentState) -> AgentState:
    markdown = state.get("report_markdown") or ""
    if not markdown.strip():
        raise ValueError("convert_markdown_to_html: report_markdown is empty")
    state["report_html"] = _markdown_to_html(markdown)
    return state
