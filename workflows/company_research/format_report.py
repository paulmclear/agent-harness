"""Persist the rendered report to the per-run output directory.

Runs after build_final_report_with_citations + convert_markdown_to_html, so
both `report_markdown` and `report_html` are populated. Mirrors the role of
fcc_intel's format_report node: write the report artefact to disk under
`state['output_dir']` so the run is inspectable without HubSpot.
"""

from __future__ import annotations

from pathlib import Path

from workflows.company_research.state import AgentState

_DEFAULT_OUTPUT_DIR = Path("output")
_MARKDOWN_FILENAME = "company_research_report.md"
_HTML_FILENAME = "company_research_report.html"


def format_report_node(state: AgentState) -> AgentState:
    markdown = state.get("report_markdown")
    html = state.get("report_html")
    if not markdown and not html:
        return state

    out_dir = Path(state.get("output_dir") or _DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    if markdown:
        (out_dir / _MARKDOWN_FILENAME).write_text(markdown, encoding="utf-8")
    if html:
        (out_dir / _HTML_FILENAME).write_text(html, encoding="utf-8")

    return state
