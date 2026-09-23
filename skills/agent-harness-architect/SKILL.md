---
name: agent-harness-architect
description: Design, spec, and architect agent harnesses — the software layer that wraps around AI models to put them on deterministic rails for production-grade reliability. Use this skill whenever the user wants to design a new agent system, plan a multi-agent workflow, spec out an agentic pipeline, choose between agent architectures (general-purpose, specialized, autonomous, hierarchical, DAG), or create a harness design document. Also trigger when the user mentions "harness", "agent architecture", "agent workflow design", "agentic pipeline", "multi-agent system design", "agent orchestration", "agent reliability", or asks how to make an agent system production-ready. This skill covers the DESIGN phase — for implementation code patterns, use the langgraph-harness-builder skill instead.
---

# Agent Harness Architect

A skill for designing and speccing agent harnesses — the software layer that guarantees AI model reliability through deterministic rails rather than hoping prompts are followed.

## What Is a Harness?

A harness wraps around an AI model, replacing hope-based prompting with deterministic process control. Instead of asking an LLM to "please do X correctly", a harness *guarantees* it by baking validation, state management, and quality loops into the surrounding software.

**Why this matters:** Agentic workflows compound failure. At 90% reliability per step, a 10-step workflow run 10x/day produces 6+ failures/day. At 99.9% per step, that drops to ~1 failure every 10 days. Harnesses are how you cross that gap.

## When to Use This Skill

Use this skill at the START of any agent harness project — before writing code. Walk the user through the full design process so they have a living spec document before implementation begins.

The output is a complete **Harness Spec Document** covering architecture, planning, agent roster, tool calling, memory, state, context management, validation, guardrails, cost budgets, and assumptions.

## Design Process

Follow these steps in order. For each section, ask the user targeted questions, offer recommendations based on their answers, and fill in the spec template.

### Step 1: Understand the Problem

Ask:
- What task or workflow does this harness automate?
- What happens today without a harness? (one-shotting, context rot, unreliable output, manual steps)
- What's the target reliability level? (90% experimental / 99% production / 99.9% business-critical)
- Is the output objectively verifiable (code, data) or subjective (writing, design, legal analysis)?

### Step 2: Select Architecture

Use the Architecture Decision Framework. Read `references/architecture-decision-framework.md` for the full flowchart, but the core logic is:

1. **Scope:** Well-defined predictable steps → Specialized. Open-ended → General-purpose. Event-triggered → Autonomous.
2. **Scale:** Needs parallel processing across many items → Hierarchical/Multi-agent or DAG. Single-threaded is fine → Keep it simple.
3. **Complexity:** Fits one context window → Single agent, minimal harness. Exceeds one window → Add context resets, sub-agents, or sprints. Multiple specialised capabilities → Multi-agent.
4. **Reliability:** 90% → Minimal harness, dynamic planning. 99% → Fixed plans, validation loops. 99.9% → Full harness with adversarial eval, human gates, test suites.
5. **Evaluation type:** Objectively verifiable → Programmatic test loops. Subjective → Adversarial evaluator with graded criteria. Mixed → Layer both.

Present the five architecture types with their trade-offs:

| Architecture | When to use | Example |
|---|---|---|
| General-purpose | Broad tasks, flexible tool use | Claude Code |
| Specialized | Fixed multi-stage workflows with gated validation | Contract review, compliance audits |
| Autonomous | Event-triggered, self-directed with memory | Monitoring bots |
| Hierarchical / Multi-agent | Coordinated swarms with supervisor | Supervisor + specialised sub-agents |
| DAG-based | Branching, conditionals, parallel execution | Pipeline orchestrators |

### Step 3: Choose Planning Strategy

| Strategy | When to use |
|---|---|
| Fixed plan | Same steps every run — deterministic rails (e.g., 8-phase contract review) |
| Dynamic plan | LLM generates/adjusts its own task list based on the request |
| Hybrid | Fixed phases with dynamic sub-steps within each phase |

Key principle: Without a plan to ground itself, long-running agents drift off track as tool calls accumulate. Default to fixed or hybrid unless the task genuinely requires full dynamic planning.

### Step 4: Design the Agent Roster

For each agent in the system, define:
- **Role** — what it does (orchestrator, sub-agent, evaluator)
- **Model** — match model tier to task complexity (see model guidance below)
- **Context budget** — how lean should its context be?
- **Tools available** — which tools does this agent need?

Model tier guidance:
| Role | Recommended tier | Examples |
|---|---|---|
| Orchestrator / Supervisor | Top-tier reasoning | Opus 4.6, Gemini 2.5 Pro |
| Sub-agents (narrow tasks) | Fast / cheap | Gemini 2.5 Flash, Haiku, Sonnet |
| Evaluator / QA | Strong reasoning | Opus 4.6, Opus 4.5 |
| Planning / Spec expansion | Strong reasoning | Opus 4.6 |

Key principle: Keep the orchestrator's context lean (< 10K tokens). Delegate verbose work to sub-agents with fresh context windows.

### Step 5: Select Tool Calling Strategy

Read `references/tech-catalogue.md` for the full tools catalogue. The four patterns:

| Pattern | When to use |
|---|---|
| Standard tool calling | Few tools, simple sequential tasks |
| Tool Search (deferred loading) | Many tools/MCPs, agent rarely needs all at once |
| Programmatic / Sandbox execution | Batch processing, loops, aggregations across many entities |
| Tool Use Examples (multi-shot) | Agent sends wrong parameter values — show it correct examples |

You can layer multiple patterns. For complex harnesses, programmatic execution inside a sandbox with a tool bridge for auth is the most scalable approach.

### Step 6: Design Memory

Three tiers to consider:

| Type | Implementation | Scope |
|---|---|---|
| Short-term / Working | Context window + compaction | Within a single run |
| Short-term / File-based | Markdown files read into system prompts | Across context resets |
| Long-term / Persistent | Vector DB, knowledge graph, or markdown files | Across sessions |

For specialized harnesses, file-based memory (progress tracking files) is essential — it's how each sub-agent or sprint knows what's been done and what's next (the Initialiser/Coder pattern).

### Step 7: Design State Management

- Choose a state tracking mechanism: LangGraph checkpointer (SqliteSaver for dev, PostgresSaver for prod), database table, JSON file, or in-memory
- Define phases/stages the harness will pass through
- Determine if the harness needs to resume from a failed phase (checkpointing)

Specialized harnesses are essentially state machines. The state machine logic lives in the harness engine code, not in prompts.

### Step 8: Plan Context Management

- Set a context budget for the main agent (target token count)
- Decide on context compaction strategy (token trimming or summarise-and-reset)
- Plan how to handle verbose tool outputs (save to files, provide summaries + navigation tools)
- Design context resets if needed (when to trigger fresh context windows)

Key principle: Context is precious. Models exhibit "context anxiety" as the window fills — they rush, wrap up prematurely, and declare things done when they're not.

### Step 9: Design Skills & Playbooks

Read `references/skills-vs-playbooks.md` for the full comparison. Two complementary knowledge layers:

**Skills** — Procedural markdown instructions injected into system prompts. Small, portable. "How to do the task." Use when something must happen every single time.

**Playbooks / Knowledge Base (RAG)** — Reference documents retrieved via RAG at specific harness phases. Large corpus. "What to check against." Use for domain knowledge the model wasn't trained on.

For each, define: what documents, which agents consume them, retrieval method (if RAG), chunking strategy, embedding model, and when in the workflow they're loaded.

### Step 10: Design Validation & Evaluation

Two distinct layers — read `references/validation-strategy.md` for details:

**Build-time evals** (does it work?):
- LangSmith evaluators — LLM-as-judge with custom criteria, dataset management, regression testing
- RAGAS metrics — faithfulness, context precision/recall, answer relevance (for RAG components)
- DeepEval tests — pytest-native CI/CD assertions with quality thresholds

**Runtime validation loops** (keep it reliable per-run):
- Programmatic tests — generate → test → fix loop (for code output)
- Adversarial evaluator agent — generator + evaluator with graded criteria (for subjective quality)
- Fact-checking loops — cross-reference against source material
- Human-in-the-loop — manual approval gates for high-stakes actions

For adversarial evaluators, define: grading criteria, weighting (weight weak areas heavier), and whether the evaluator can interact with output (e.g., Playwright MCP for testing web UIs).

### Step 11: Design Guardrails

Three layers of runtime controls:
1. **Pre-processing (input):** Banned keywords, PII detection, prompt injection blocking, rate limiting
2. **In-processing (during):** Tool parameter validation, business rule enforcement, HITL approval for sensitive tools
3. **Post-processing (output):** Content moderation, toxicity check, hallucination check, format validation

Recommended stack: LangChain Middleware (custom logic + HITL) + NeMo Guardrails (dialogue control + safety) + Guardrails AI (output validation). Layer them: deterministic checks first (cheap), model-based checks second (expensive).

### Step 12: Set Budgets & Log Assumptions

**Cost & performance budget:**
- Total token budget across all agents
- Main agent token budget (keep lean)
- Time budget per run
- Cost ceiling per run

**Assumptions log:** Every harness component encodes an assumption that the model can't do X. Track these so you can simplify as models improve.

| Assumption | Component it drives | Status |
|---|---|---|
| Model drifts in long sessions | Context resets | Active / Stale |
| Model can't self-evaluate | Adversarial evaluator | Active / Stale |
| Model can't handle N items in one pass | Sub-agent parallelisation | Active / Stale |

### Step 13: Run the Project Checklist

Read `references/project-checklist.md` and walk the user through the pre-build checklist to confirm nothing is missing before implementation begins.

## Output Format

The final output should be a complete Harness Spec Document. Read `references/harness-spec-template.md` for the full template with all sections and placeholder fields.

## Key Principles (Reference Card)

Keep these in mind throughout the design process:

1. **Harness > Prompting** — Don't hope the AI follows instructions; guarantee it with deterministic rails
2. **Context is precious** — Keep the main agent lean; delegate verbose work to sub-agents
3. **Plan or drift** — Without a plan, long-running agents lose the plot
4. **Verify, don't trust** — Self-evaluation is unreliable; use adversarial evaluation or programmatic tests
5. **Assumptions go stale** — Every component encodes a model limitation; revisit as models improve
6. **Simplest solution possible** — Don't over-engineer; add complexity only when demonstrably needed
7. **Parallel > Sequential** — Sub-agents in parallel protect context and save time
8. **Programmatic output > LLM output** — Generate final deliverables from templates where possible
9. **Weight evaluator criteria toward weaknesses** — Score harder on what the model struggles with
10. **Contract negotiation** — For multi-sprint work, agree the definition of done upfront

## Reference Files

Read these as needed during the design process:
- `references/harness-spec-template.md` — The full spec template with all sections and placeholders
- `references/architecture-decision-framework.md` — Detailed flowchart for architecture selection
- `references/tech-catalogue.md` — Tools, frameworks, and models mapped to harness components
- `references/skills-vs-playbooks.md` — When to use skills vs RAG-based playbooks
- `references/validation-strategy.md` — Build-time evals and runtime validation patterns
- `references/project-checklist.md` — Pre-build, during-build, and post-build checklists

## Preferred Technology Stack

The default stack for all new harness projects (unless there's a strong reason to deviate):
- **LangGraph** — Orchestration engine (stateful, cyclical graphs with checkpointing)
- **LangChain** — Agent primitives (chains, tools, prompts, memory, model wrappers)
- **LangSmith** — Observability & evaluation (tracing, debugging, eval datasets, cost tracking)
- **RAGAS** — RAG-specific evaluation (faithfulness, context precision/recall, answer relevance)
- **DeepEval** — CI/CD test runner (pytest-native LLM assertions, red-teaming)
- **LangChain Middleware + NeMo Guardrails + Guardrails AI** — Runtime controls
