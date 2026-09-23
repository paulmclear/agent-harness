---
name: agent-memory-design
description: Design and implement memory systems for agent harnesses — covering short-term working memory, file-based memory across context resets, long-term persistent memory (vector stores, knowledge graphs), context management strategies (compaction, summarisation, resets), and handoff patterns between agents or sprints. Use this skill whenever the user wants to design how an agent remembers things, manage context window budgets, implement context compaction or summarisation, set up the Initialiser/Coder handoff pattern, use progress tracking files between agent sessions, build long-term memory with vector databases or knowledge graphs, handle context anxiety in long-running agents, implement sprint-based memory handoffs, or decide between in-context memory vs file-based vs persistent storage. Trigger on mentions of "agent memory", "context management", "context window", "context budget", "context compaction", "context anxiety", "context resets", "progress tracking", "handoff pattern", "sprint handoffs", "long-term memory", "vector store memory", "knowledge graph memory", "working memory", "file-based memory", "state persistence", "checkpointing", or any request about how agents should remember, forget, or manage information across runs.
---

# Agent Memory Design

A skill for designing memory systems that let agents maintain knowledge within runs, across context resets, and across sessions — while keeping context windows lean and agents on track.

## Why Memory Design Matters

Memory is how agents avoid starting from scratch every time. Without deliberate memory design, agents either drown in accumulated context (context rot) or lose critical information between sessions. Both lead to failures.

The core tension: **models perform best with focused, relevant context** but complex tasks generate lots of intermediate data. Memory design is about resolving this tension — keeping the right information available at the right time.

## Memory Taxonomy

Three tiers, each solving a different problem:

| Tier | Scope | Persistence | Implementation | Solves |
|---|---|---|---|---|
| **Working memory** | Within a single run | Context window | Messages + state object | Keeping track of the current task |
| **File-based memory** | Across context resets | Filesystem | Markdown/JSON files read into prompts | Surviving context resets without losing progress |
| **Long-term memory** | Across sessions | Database | Vector store, knowledge graph, or persistent files | Recalling past work, learning from experience |

## Decision Framework

Use this to choose the right memory strategy for your harness:

### Question 1: Does the task fit in one context window?

**Yes** → Working memory is sufficient. Use LangGraph state with `add_messages` reducer. Add token trimming if conversations get long.

**No** → You need file-based memory or context resets. Continue to Question 2.

### Question 2: Is the task a single long session or multiple distinct phases?

**Single long session** (e.g., building an app over hours) → Context compaction (summarise-and-reset) within a single run. Read `references/context-management.md`.

**Multiple phases with handoffs** (e.g., sprints, multi-agent workflows) → File-based memory with progress tracking. Read `references/handoff-patterns.md`.

### Question 3: Does the agent need to learn from past runs?

**No** → Skip long-term memory. Working memory + file-based memory is enough.

**Yes** → Add a vector store or knowledge graph for cross-session recall. Read `references/long-term-memory.md`.

### Question 4: Is the agent autonomous (event-driven)?

**No** → Standard memory patterns apply.

**Yes** → The agent needs to read memory on every trigger to decide what to do. Autonomous agents like OpenClaw read from persistent memory at the start of each invocation to reconstruct context. Read `references/long-term-memory.md`.

## Tier 1: Working Memory (Within a Run)

Working memory is the agent's context window — the messages, state, and tool outputs accumulated during a single run.

### LangGraph State as Working Memory

In LangGraph, the `State` object IS your working memory. Every node reads from and writes to it.

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class HarnessState(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation history
    phase: str                                # Current phase
    extracted_data: dict                      # Intermediate results
    analysis: dict                            # Analysis output
```

**Key principle:** Only put information in state that downstream nodes actually need. Don't accumulate everything — that's how context rot starts.

### When Working Memory Isn't Enough

Watch for these signals:
- **Context anxiety** — The model rushes, wraps up prematurely, or declares things done when they're not. This happens as the context window fills.
- **Quality degradation** — Outputs get worse as the conversation grows. The model loses track of early instructions.
- **Token budget exceeded** — You're approaching the model's context limit.

When these appear, you need context management. Read `references/context-management.md`.

## Tier 2: File-Based Memory (Across Context Resets)

File-based memory bridges the gap between context resets. Write progress to files; the next agent session reads those files to pick up where things left off.

### The Initialiser/Coder Pattern

The foundational pattern for multi-session work. Read `references/handoff-patterns.md` for complete implementation.

1. **Initialiser agent** — Sets up environment, breaks project into features, creates a progress tracking file
2. **Coder agent** — Reads the progress file, works one feature at a time, commits to git, updates progress for the next session

### Progress Tracking File

```json
{
  "project": "Contract Review Harness",
  "created_at": "2026-03-29T10:00:00Z",
  "features": [
    {"id": "F001", "name": "Text extraction", "status": "complete"},
    {"id": "F002", "name": "Classification", "status": "complete"},
    {"id": "F003", "name": "Risk analysis", "status": "in_progress"},
    {"id": "F004", "name": "Report generation", "status": "pending"}
  ],
  "current_feature": "F003",
  "context_summary": "Extracted 34 clauses from NDA. Classified as employment contract. 12/34 clauses analysed for risk so far.",
  "decisions_log": [
    "Chose parallel sub-agents for clause analysis (too many for single pass)",
    "Using Gemini Flash for sub-agents to save cost"
  ]
}
```

### When to Use File-Based Memory

- Multi-sprint builds where each sprint is a fresh context window
- Context resets triggered by length (the "Opus 4.5 pattern")
- Multi-agent workflows where agents hand off to each other
- Any harness that runs longer than a single context window can support

## Tier 3: Long-Term Memory (Across Sessions)

Long-term memory persists across separate harness runs. The agent can recall past tasks, learn from outcomes, and apply accumulated knowledge.

Read `references/long-term-memory.md` for complete implementation patterns covering vector stores, knowledge graphs, and autonomous agent memory.

## Context Management Strategies

The most critical memory design decision for long-running agents. Read `references/context-management.md` for all strategies in detail.

Quick summary of the four approaches:

| Strategy | How it works | Best for | Trade-off |
|---|---|---|---|
| **Token trimming** | Keep last N tokens, drop oldest messages | Moderate conversations | Loses old context permanently |
| **Summarise-and-reset** | Compress history into summary, keep recent messages | Very long sessions | Summary may lose critical details |
| **File-based offloading** | Save verbose outputs to files, keep summaries in context | Verbose tool outputs | Agent must know to check files |
| **Context resets** | Fresh context window, read progress file | Multi-sprint work | Requires progress tracking |

## Key Principles

1. **Context is precious** — Keep the main agent's context lean. Every token of irrelevant context is a token of relevant context displaced.

2. **Don't trust the model to manage its own context** — Models exhibit context anxiety as windows fill. Build context management into the harness, not into the prompt.

3. **Verbose outputs go to files** — Tool responses, API results, and intermediate data should be saved to files with summaries in context. Give the agent tools to read details on demand.

4. **Progress tracking enables resilience** — If the harness can crash at any point and resume from a progress file, you've built a resilient system.

5. **Memory has diminishing returns** — Don't over-invest in long-term memory unless the agent genuinely benefits from cross-session recall. Most harnesses only need working memory + file-based memory.

6. **Assumptions go stale** — Opus 4.6 (1M context) eliminated the need for context resets that Sonnet 4.5 required. Revisit your memory design as models improve.

## Reference Files

- `references/context-management.md` — All context management strategies in depth: token trimming, summarise-and-reset, file offloading, context resets, and choosing between them
- `references/handoff-patterns.md` — The Initialiser/Coder pattern, sprint-based handoffs, progress tracking files, and multi-agent memory coordination
- `references/long-term-memory.md` — Vector store memory, knowledge graph memory, autonomous agent memory, and cross-session recall patterns
