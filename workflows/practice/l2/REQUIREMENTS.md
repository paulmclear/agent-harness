# Level 2: IT Service Desk Incident Triage — Requirements

Legend: F = fully addressed, P = partly addressed, N = not addressed, D = deliberate deviation (see linked ADR).

## Input

- [F] Workflow accepts a `SupportTicket` with fields: `ticket_id`, `employee_id`, `subject`, `description`.

## Output

- [F] Workflow produces a `TriageDecision` with fields: `ticket_id`, `category`, `priority`, `assigned_team`, `suggested_response`, `knowledge_articles`, `needs_human_review`. *(named `TriageOutput`; has all required fields plus extra `*_confidence` fields)*
- [P] `TriageDecision.ticket_id` matches the input `SupportTicket.ticket_id`. *(true on the security path; ordinary path never constructs a `TriageOutput` at all)*
- [P] Both the ordinary support path and the security path converge on the same `TriageDecision` type. *(security path builds `TriageOutput`; ordinary path's `triage_agent` writes an unrelated `example_agent_output` key, not `triage_output`)*

## Business tool interfaces (treat as existing/deterministic; do not reimplement internals)

- [F] `get_employee(employee_id: str) -> Employee` is available, returning `employee_id`, `name`, `department`, `office`, `device_id`. *(model uses `device_ids: list[str]` instead of singular `device_id`, plus adds `email`)*
- [F] `get_device(device_id: str) -> Device` is available, returning `device_id`, `os`, `managed`, `last_seen`.
- [F] `search_kb(query: str) -> list[KnowledgeArticle]` is available, returning articles with `article_id`, `title`, `summary`, `content`. *(implemented and tested in isolation; no node calls it yet — see below)*
- [F] `get_support_team(category: str) -> SupportTeam` is available for categories: `vpn`, `email`, `hardware`, `software`, `identity`, `network`, `other`. *(signature differs — takes `(category, security_related)` and returns a plain string, not a `SupportTeam` type — but no node calls it yet either)*
- [P] `classify_security_risk(ticket: SupportTicket) -> SecurityRisk` is available, returning `security_related: bool` and `reason: str`. *(implemented as a probabilistic TypeSafe LLM judgment rather than the "existing deterministic service" the spec describes; returns an enum `reason` + confidence scores, not a free-text `reason`)*

## Routing / orchestration

- [F] Every ticket is evaluated by `classify_security_risk` before determining its final path.
- [F] If `SecurityRisk.security_related == True`, the workflow takes the security path and does not run normal IT triage logic on that ticket.
- [F] Security-path tickets are always assigned `assigned_team = "Cyber Security Operations"`.
- [F] Security-path tickets always set `needs_human_review = True`.
- [P] Non-security tickets are eligible for the ordinary support path (KB search, category classification, response generation). *(category classification is wired; KB search and response generation are not — `triage_agent` is a leftover research-assistant template unrelated to triage)*
- [D] The workflow decides, per ticket, whether knowledge-base retrieval is warranted (RAG is optional, not mandatory, on this path). *(challenged: the KB is always searched; the per-ticket decisions are whether the results are usable and whether to escalate to an agent search — see [ADR-001](docs/adr-001-always-search-kb.md))*
- [F] The graph expresses conditional routing (a branch point), not a single linear chain.

## Ordinary support path

- [F] The workflow determines a `category` for the ticket from the valid category set used by `get_support_team`. *(`classify_ticket_node`)*
- [P] The workflow determines a `priority` for the ticket. *(computed in `classify_ticket_node`, but values `critical/high/medium/low` don't match `TriageOutput`'s `Literal["low","normal","high","critical"]` — "medium" would fail validation — and the value is never carried into `triage_output` on this path)*
- [N] The workflow determines an `assigned_team` via `get_support_team(category)`. *(no node calls `get_support_team` on this path)*
- [N] When KB retrieval is performed, `search_kb` results feeding the decision are reflected in `knowledge_articles` (by `article_id`). *(`kb_lookup` now calls `search_kb` and `grade_articles` grades the results, but nothing populates `knowledge_articles` yet)*
- [N] The workflow generates a `suggested_response` for the ticket. *(`triage_agent` produces an unrelated three-bullet "research brief" and doesn't write to `triage_output`)*
- [N] `needs_human_review` is set appropriately (not hardcoded True) for tickets on this path. *(never set at all on this path — no `triage_output` is built)*

## Explicit non-goals for Level 2

- [F] No multi-agent orchestration.
- [F] No subgraphs.
- [F] No human-approval workflows.
- [F] No cross-ticket memory.
- [F] No write operations to external systems.
- [F] No complex error-recovery logic.

## Implementation constraint

- [F] Orchestration is implemented as a LangGraph graph (not a single linear chain), reflecting the conditional-routing requirement above.
