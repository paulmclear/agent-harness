# ADR-001: Always search the knowledge base on the ordinary support path

- **Status:** Accepted (pending Product Owner sign-off on the requirement change)
- **Date:** 2026-09-23
- **Scope:** `workflows/practice/l2` — ordinary (non-security) triage path

## Context

`REQUIREMENTS.md` states:

> The workflow decides, per ticket, whether knowledge-base retrieval is warranted (RAG is optional, not mandatory, on this path).

The triage output includes a `suggested_response` that a service-desk agent may act on directly. It is only trustworthy if it is grounded in approved KB content.

`search_kb` stands in for an external API/MCP lookup: we do not control its ranking. The current implementation scores by naive keyword overlap and returns anything with a score above zero, so raw results include off-topic matches and miss paraphrases ("can't log in" vs. "password reset").

We also needed to decide how much of the KB work belongs to an LLM agent versus deterministic steps in the graph.

## Decision

1. **Always search.** Every ordinary-path ticket runs a deterministic first-pass lookup (`kb_lookup`): `search_kb(subject + description + category)`, top `kb_lookup_limit` (default 3). The category term matches article tags, which `search_kb` weights highest, so it favours same-category articles without filtering others out.
2. **One relevance judge.** A TypeSafe node (`grade_articles`) rates each candidate `direct` / `partial` / `none` with a confidence. It is the only component whose relevance judgment feeds routing or output.
3. **Escalate on a miss.** If no candidate is `direct`, the graph routes once to `kb_search_agent`, a tool-calling agent that rewrites queries (max 3 `search_kb` calls, enforced by the harness, stopping at its first plausible hit; category passed as a hint only). Its picks go back through `grade_articles`. A `kb_escalated` flag prevents a second escalation.
4. **Grounded or nothing.** The tool-free `triage_writer` runs only when at least one article is `direct` or `partial`. Otherwise `suggested_response` is `None` and the ticket goes to human review.
5. **Code checks citations.** `build_triage_output` drops any cited article ID that was not graded, and forces human review if it drops one.

The requirement's "decide per ticket" intent is kept, but moved: the graph decides *whether retrieval found something usable* and *whether to escalate*, rather than *whether to look*.

## Rationale (the case for the Product Owner)

- **Grounding.** Without KB context the writer's response relies on the model's general knowledge: higher risk of hallucination and inconsistent answers across similar tickets.
- **Cost.** The common path is one deterministic lookup plus one TypeSafe grading call. The agent loop, the expensive part, runs only when the first pass misses.
- **Noise is handled, not avoided.** The usual argument for optional RAG is that irrelevant context degrades answers. Grading addresses that directly: `none` articles never reach the writer, and a ticket with nothing relevant gets no suggested response rather than a stretched one.
- **Measurability.** Each step has a typed output that can be evaluated on its own: lookup recall, grading precision, agent recovery rate on misses, and writer faithfulness.

## Alternatives considered

| Option | Why not |
|---|---|
| **A. Optional search, per requirement** (`should_search_kb` judgment before retrieval) | Adds a judgment that is hard to get right ("laptop won't power on" looks like hardware but has a KB article) and saves little, since a lookup is cheap. A wrong "no" silently removes grounding. |
| **B. Deterministic only** (lookup + grade, no agent) | Cheapest and fully reproducible, but no recovery when keyword search misses because of wording. |
| **C. Agent owns all retrieval** (agent with `search_kb` tool on every ticket) | Best at recovering from wording mismatches, but costs 2–4 LLM calls on every ticket, varies from run to run, and hides relevance inside the agent where routing can't see it. Undermines the "search is cheap" argument. |

Chosen: **B with C as a fallback**.

## Consequences

- **Positive:** every suggested response is grounded or absent. Relevance becomes an explicit signal for the `human_action` / `human_review` decision. Most tickets make no agent calls.
- **Negative:** deviates from the written requirement and needs sign-off. Tickets that escalate take longer and cost more. Article selection on escalated tickets varies between runs (accepted; we measure precision and recall and revisit if evals show too much variation).
- **Implemented (2026-09-23):** `kb_lookup`, `grade_articles`, `kb_search_agent`, `triage_agent` (the writer), `build_triage_output`, and `route_after_grading`. The `human_action` thresholds live in `config.py`. One tightening from the original design: the reply must *cite* a `direct` article, not just have one available.
- **Follow-ups:** per-step eval datasets (grading precision, agent recovery on misses, writer faithfulness), and a check of how much article selection varies between runs.
