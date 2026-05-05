# Improvements — HubSpot Company Research workflow

Backlog of architectural changes worth making to this workflow. Ordered by
leverage (return on engineering time), not by topic.

## Structured outputs

Today every LLM-produced JSON in this workflow is coaxed via "Return valid
JSON" instructions and parsed back with fence-tolerant regex
(`_parse_batch_payload`, `_parse_builder_output`, the JSON-fence handling in
`merge_gap_data_node`). When a model adds a preamble, omits the fence, or
drifts the schema, we silently fall back to lossy defaults. Pydantic +
`.with_structured_output()` replaces this with a hard contract.

### 1. `build_final_report_with_citations.py` — high value

**Today:** Returns `{report, companyId, companyName, scoring, totalCitations,
researchDate}` via JSON-in-prompt; `_parse_builder_output` looks for raw JSON,
then a ```json fence, then falls back to "treat the whole response as
markdown." On that fallback we lose `scoring_summary` silently.

**Change:** Define `FinalReport(BaseModel)` with `report: str`,
`scoring: ScoringSummary`, `total_citations: int`, `research_date: str`. Use
`ChatOpenAI(model="gpt-5.1", reasoning={"effort": "low"}).with_structured_output(FinalReport)`.
Drop `_JSON_FENCE`, `_parse_builder_output`, and the JSON template at the
bottom of the prompt. gpt-5.1 supports this natively.

### 2. `ai_agent_fill_gaps.py` — high value

**Today:** Tool-using `create_agent` returns `{"filled_data": {<field>:
{value, source}}}` as the final assistant message; `merge_gap_data_node`
runs fence-tolerant JSON parsing on it.

**Change:** Define `GapFillerResponse(BaseModel)` with
`filled_data: dict[str, FilledField]`. Constrain the agent's *final*
response (LangChain's `response_format=` parameter on `create_agent`, or
pipe the agent's last message through a `.with_structured_output()` call).
After this, `merge_gap_data_node` reads `state["filled_data"]` as a dict
directly — the regex/JSON-parse block goes away.

### 3. The six `research_batch_*` agents — medium value

**Today:** Each batch returns free-form JSON that
`extract_deduplicate_citations_node` parses to dedupe citations, and that
`detect_data_gaps_node` walks via dotted paths
(`corporate_intelligence.employee_count`, `.annual_revenue`,
`.recent_acquisitions`). Schema drift here breaks gap detection silently.

**Constraint:** Perplexity sonar-pro's structured-output support through
`langchain-perplexity` is patchy.

**Change (option A, conservative):** Define Pydantic models per batch
(`CorporateIntelligence`, `OpportunitySignals`, `InternalAnalysis`,
`RelationshipIntelligence`, `CommercialIntelligence`,
`StrategicAssessment`). Try `.with_structured_output()` first; on failure,
keep the current fence-tolerant parser but validate the resulting dict
against the Pydantic model inside `extract_deduplicate_citations_node`. The
contract becomes load-bearing either way.

**Change (option B, more invasive):** Replace Perplexity sonar-pro with
gpt-5-mini bound to a web-search tool. Native structured outputs, but you
lose Perplexity's grounded-search quality and citation density.

### 4. The seven analyst agents — skip for now

**Today:** Each returns a JSON blob that is passed *as text* into
`build_final_report`, which is itself an LLM that's told to "Parse agent
JSON outputs properly."

**Why skip:** A structured output here unlocks nothing on its own — the
text just gets re-tokenised inside the next LLM. The win only materialises
if you also rip out the final-builder LLM (see "Deterministic final
report" below).

## Deterministic final report — medium value, bigger refactor

`build_final_report_with_citations` is the only LLM hop after the analyst
fan-in. It exists to assemble seven JSON blobs into a single markdown
document. That assembly is templating — Python can do it.

**Change:**

1. Give each of the seven analyst agents a Pydantic model
   (`OverviewFindings`, `RegulatoryNews`, `StakeholderAnalysis`,
   `OpportunityAssessment`, `DetailedScoring`, `CampaignsServices`,
   `EngagementOutreach`).
2. Bind each via `.with_structured_output()`; store typed dicts on state
   instead of raw strings.
3. Replace `build_final_report_node` with a pure Python function that
   renders the markdown from the typed inputs plus the citation registry.

**Wins:**
- One fewer LLM call per run (cost + latency).
- `state["scoring_summary"]` becomes load-bearing — you can read
  `agent_5_scoring.overall_score` directly without a second LLM
  re-extracting it.
- Report layout is deterministic, version-controlled, and testable
  without burning tokens.

**Cost:** ~½ day of work; need to lock down each analyst's schema and
write the renderer.

## State as Pydantic — low value, stylistic

`AgentState` is currently a `TypedDict` with `Annotated[..., _keep_first]`
reducers. LangGraph supports `BaseModel` state with the same reducer
mechanics. Worth doing if/when we add cross-cutting validation (e.g.
"`employees` must be `>= 0`"); not worth doing just for typing.

## Other items not related to structured outputs

### Citation enrichment from gap-fill sources

`merge_gap_data_node` has a port note from the n8n spec: the gap-filler's
`filled_data[*].source` URLs are *not* being appended to the citation
registry. Today they're discarded. Fix: walk `filled_data.values()`, append
unique URLs to `state["citations"]` with the next monotonic id, and bump
`state["total_citations"]`.

### Trigger model

The graph runs against a `company_id` passed at invocation — the n8n
`hubspot.company.propertyChange` trigger isn't modelled. Two options:

- **CLI/script invocation only** (current): keep as-is, document that the
  workflow is invoked externally (cron, FastAPI endpoint, queue worker).
- **Webhook server**: add a tiny FastAPI app that receives HubSpot
  webhooks and calls `graph.invoke(...)` with the property-change payload.
  The `_check_status_value` router already handles the loop-prevention
  case for `propertyValue == "Updated"`.

### Markdown→HTML converter robustness

`convert_markdown_to_html_node` is a regex-based port of the n8n spec's
regex transform. Acceptable for the report shapes we control, but brittle
if the final-builder LLM ever emits nested lists, code blocks, or
non-trivial table content. The spec itself flags this as a port target —
swap for `markdown-it-py` or `marked` when convenient. Pure-code change,
no LLM impact.

### Concurrency and cost ceiling

Six Perplexity calls + seven OpenAI calls + (optionally) one tool-using
agent + one final builder = up to 15 LLM calls per company, fanned out via
LangGraph's default executor. There's no per-run cost ceiling or
rate-limit retry today. Worth adding before this is invoked at HubSpot
trigger volume (n8n spec caps at 5 concurrent executions for a reason).
