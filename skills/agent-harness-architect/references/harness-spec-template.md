# Harness Spec Template

Copy this template and fill in each section to create a complete harness design document.

---

## Harness Name

`[Project Name] Harness`

## Purpose & Scope

- **What problem does this harness solve?**
- **What would happen without the harness?** (one-shotting, context rot, unreliable output)
- **Target reliability level:** 90% / 99% / 99.9% per step

## Architecture Choice

| Architecture | When to use |
|---|---|
| General-purpose | Broad tasks, flexible tool use (e.g. Claude Code) |
| Specialized | Fixed multi-stage workflows with gated validation (e.g. contract review) |
| Autonomous | Event-triggered, self-directed with memory |
| Hierarchical / Multi-agent | Coordinated swarms with supervisor |
| DAG-based | Branching, conditionals, parallel execution |

**Selected architecture:** `[Choose one]`
**Rationale:** `[Why this fits your problem]`

## Planning Strategy

- **Fixed plan:** Same steps every run (deterministic rails)
- **Dynamic plan:** LLM generates/adjusts its own task list
- **Hybrid:** Fixed phases with dynamic sub-steps within each

**Selected:** `[Choose one]`

## Agent Roster

| Agent | Role | Model | Context budget | Tools available |
|---|---|---|---|---|
| Orchestrator | Coordinates workflow, manages state | e.g. Opus 4.6 | Lean (< 10K) | State management, delegation |
| Sub-agent 1 | `[Specific task]` | e.g. Gemini 2.5 Flash | Full | `[Relevant tools]` |
| Evaluator | QA / adversarial review | e.g. Opus 4.6 | Fresh per eval | Playwright MCP, screenshots |

## Tool Calling Strategy

| Pattern | When to use |
|---|---|
| Standard tool calling | Few tools, simple sequential tasks |
| Tool Search (deferred loading) | Many tools/MCPs, agent rarely needs all at once |
| Programmatic / Sandbox execution | Batch processing, loops, aggregations across many entities |
| Tool Use Examples (multi-shot) | Agent sends wrong parameter values |

**Selected pattern(s):** `[Choose one or layer multiple]`

## Memory Design

| Type | Implementation | Scope |
|---|---|---|
| Short-term / Working | Context window + compaction | Within a single run |
| Short-term / File-based | Markdown files read into system prompts | Across context resets |
| Long-term / Persistent | Vector DB, knowledge graph, or markdown files | Across sessions |

## State Management

- **State tracking mechanism:** `[LangGraph checkpointer (SqliteSaver / PostgresSaver) / Database table / JSON file / in-memory]`
- **Phases/stages:** `[List the phases, e.g. Extract → Classify → Analyse → Generate → Review]`
- **Checkpointing:** `[Can the harness resume from a failed phase?]`

## Context Management Strategy

- **Context budget for main agent:** `[Target token count]`
- **Context compaction:** `[Yes/No — method]`
- **Context resets:** `[Yes/No — when triggered]`
- **Verbose output handling:** Save to files, provide summaries + navigation tools

## Skills & Playbooks

### Agent Skills
- **Skills used:** `[List skill files, e.g. legal/contract-review.md, finance/budget-analysis.md]`
- **Skill scope:** `[Which agents consume which skills? Orchestrator vs sub-agents?]`
- **Skill format:** `[Markdown / structured prompt / YAML]`

### Playbooks / Knowledge Base (RAG)
- **Knowledge base contents:** `[List document types, e.g. company SOPs, legal precedents, compliance policies]`
- **Retrieval method:** `[Vector store (which?), hybrid search, knowledge graph]`
- **Chunking strategy:** `[Chunk size, overlap, splitter type]`
- **Embedding model:** `[e.g. text-embedding-3-large, Cohere embed-v3]`
- **When loaded:** `[Which phase triggers retrieval?]`
- **Retrieval scope:** `[Which agents query the knowledge base?]`
- **Eval:** `[RAGAS metrics on retrieval quality]`

## Validation & Evaluation

### Runtime Validation Loops

| Method | Applies to | How |
|---|---|---|
| Programmatic tests | Code output | Generate → test → fix loop |
| Adversarial evaluator agent | Subjective quality | Generator + Evaluator with graded criteria |
| Fact-checking loops | Factual claims | Cross-reference against source material |
| Human-in-the-loop | High-stakes actions | Manual approval gates |

**Evaluator design (if applicable):**
- Criteria: `[List graded criteria, e.g. accuracy, originality, craft, functionality]`
- Weighting: `[Weight weak areas heavier to compensate]`
- Interaction: `[Can the evaluator interact with output? e.g. Playwright MCP]`

### Build-time Eval Plan
- LangSmith evaluators: `[List LLM-as-judge criteria]`
- RAGAS metrics (if RAG): `[faithfulness, context precision, context recall, answer relevance]`
- DeepEval tests: `[List CI/CD test assertions and quality thresholds]`
- Eval dataset: `[Describe dataset — size, source, coverage]`

## Runtime Controls (Guardrails)

- **Pre-processing:** `[Input validation, PII detection, prompt injection blocking, banned keywords]`
- **Tool-level:** `[Business rule enforcement, HITL approval for which tools?]`
- **Post-processing:** `[Output moderation, toxicity check, format validation, hallucination check]`
- **Libraries used:** `[LangChain Middleware / NeMo Guardrails / Guardrails AI / LLM Guard]`
- **Monitoring:** `[Track guardrail triggers in LangSmith — false positive rate target?]`

## Human-in-the-Loop Touchpoints

- `[Where does the user provide input? e.g. clarifying questions before analysis]`
- `[What requires manual approval? e.g. external API calls, publishing]`

## Sandboxing & Code Execution

- **Sandbox tool:** `[e.g. LLM Sandbox / Docker]`
- **Tool bridge:** `[How do sandbox scripts call back to host tools?]`
- **Security:** `[No direct internet, session-ID auth, locked-down endpoints]`

## System Prompts

- **Key prompt strategies per agent:** `[e.g. Orchestrator gets lean routing prompt; sub-agents get skill + playbook context; evaluator gets grading criteria]`

## Cost & Performance Budget

| Metric | Target |
|---|---|
| Total token budget | `[e.g. ~300K across all agents]` |
| Main agent tokens | `[e.g. < 10K]` |
| Time budget | `[e.g. < 30 min]` |
| Cost ceiling | `[e.g. < $50 per run]` |

## Assumptions Log

| Assumption | Component it drives | Status |
|---|---|---|
| Model drifts off track in long sessions | Context resets | `[Active / Stale]` |
| Model can't self-evaluate quality | Adversarial evaluator | `[Active / Stale]` |
| Model can't handle N items in one pass | Sub-agent parallelisation | `[Active / Stale]` |
