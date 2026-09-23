---
name: langgraph-harness-builder
description: Build agent harnesses using the LangGraph + LangChain + LangSmith stack. Use this skill whenever the user wants to implement an agent harness, build a LangGraph workflow, create a stateful agent graph, wire up tool calling with ToolNode, implement checkpointing and state persistence, build fan-out/fan-in parallel processing, compose subgraphs, implement context compaction, set up the adversarial generator-evaluator loop, or write any LangGraph/LangChain agent code. Trigger on mentions of "LangGraph", "StateGraph", "agent graph", "build the harness", "implement the harness", "wire up the agent", "tool calling loop", "checkpointing", "context compaction", "fan-out", "subgraph", or any request to write Python code for an agent workflow. This skill covers IMPLEMENTATION — for design and architecture decisions, use the agent-harness-architect skill instead.
---

# LangGraph Harness Builder

Best-practice Python code patterns for building agent harnesses using the preferred stack: **LangGraph + LangChain + LangSmith**.

## When to Use This Skill

Use this skill when the user has a harness design (or enough context to start building) and needs implementation code. This skill provides production-ready patterns for every harness component — orchestration, tool calling, memory, state, context management, and validation loops.

## Core Concepts

Before diving into patterns, understand these LangGraph fundamentals:

- **StateGraph** — The core abstraction. Define typed state, add nodes (functions or subgraphs), wire edges (deterministic or conditional). Compile to get a runnable graph.
- **State with Reducers** — State fields can have reducers that define how concurrent updates merge (e.g., `add_messages` appends, `operator.add` concatenates lists).
- **Conditional Edges** — Route to different nodes based on state values. This is how you implement branching, retry loops, and dynamic workflows.
- **Checkpointer** — Persist state to SQLite (dev) or PostgreSQL (prod). Enables resume-from-failure, human-in-the-loop pauses, and time-travel debugging.
- **ToolNode** — Pre-built node that auto-executes tool calls from the model's response. Pair with `tools_condition` for the standard agent loop.

## Pattern Selection Guide

Choose the right pattern based on what you're building:

| What you need | Pattern | Reference file |
|---|---|---|
| Simple linear pipeline (A → B → C) | Minimal Linear Graph | `references/orchestration-patterns.md` |
| Branching based on classification/state | Conditional Routing | `references/orchestration-patterns.md` |
| Process many items in parallel | Fan-out / Fan-in with `Send` | `references/orchestration-patterns.md` |
| Embed a reusable sub-workflow | Subgraph Composition | `references/orchestration-patterns.md` |
| Standard ReAct agent with tools | ToolNode Agent Loop | `references/tool-calling-patterns.md` |
| Structured tool inputs with validation | Pydantic Tool Schema | `references/tool-calling-patterns.md` |
| Batch operations in sandbox | Programmatic Tool Calling | `references/tool-calling-patterns.md` |
| Fix agent tool misuse | Multi-shot Tool Examples | `references/tool-calling-patterns.md` |
| Typed state with merge logic | State Schema with Reducers | `references/memory-state-patterns.md` |
| Resume from failure / HITL pauses | Checkpointing | `references/memory-state-patterns.md` |
| Keep context window lean | Context Compaction | `references/memory-state-patterns.md` |
| Persist knowledge across sessions | Long-term Vector Store | `references/memory-state-patterns.md` |
| Quality loop for subjective output | Adversarial Evaluator Loop | `references/orchestration-patterns.md` |

## Building a Harness: Step by Step

### 1. Define Your State

Start by defining the typed state that flows through the graph. This is your data contract between nodes.

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class HarnessState(TypedDict):
    messages: Annotated[list, add_messages]  # Chat history
    phase: str                                # Current phase
    # Add fields for your harness's intermediate and final outputs
```

Read `references/memory-state-patterns.md` for custom reducers, deep-merge patterns, and state design best practices.

### 2. Define Node Functions

Each node receives state and returns a partial state update. Only include fields you want to change.

```python
def my_node(state: HarnessState) -> dict:
    # Do work using state values
    result = process(state["input_data"])
    # Return only the fields that changed
    return {"output_data": result, "phase": "step_complete"}
```

### 3. Build the Graph

Wire nodes together with edges. Read `references/orchestration-patterns.md` for the full set of patterns.

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(HarnessState)
builder.add_node("step_1", step_1_fn)
builder.add_node("step_2", step_2_fn)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", END)
graph = builder.compile()
```

### 4. Add Tool Calling (if needed)

Read `references/tool-calling-patterns.md` for the ToolNode agent loop, structured schemas, sandbox patterns, and multi-shot examples.

### 5. Add Checkpointing (if needed)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "run-001"}}
    result = graph.invoke(initial_state, config)
```

### 6. Add Context Management (if needed)

Read `references/memory-state-patterns.md` for token trimming, summarise-and-reset, and long-term memory patterns.

## Key Implementation Principles

1. **State is the single source of truth** — All data flows through the typed state object. Nodes read from state and return partial updates. No side-channel communication.

2. **Nodes should be pure-ish functions** — Given the same state, a node should produce the same output (modulo LLM non-determinism). This makes debugging and testing much easier.

3. **Use reducers for concurrent updates** — When multiple nodes update the same field (e.g., fan-out/fan-in), define a reducer to merge results correctly.

4. **Compile once, invoke many** — Build and compile the graph once. Call `graph.invoke()` or `graph.stream()` for each run. Don't rebuild the graph per request.

5. **Always use a checkpointer for HITL** — Without a checkpointer, `interrupt_before` / `interrupt_after` won't work. Use `SqliteSaver` for dev, `PostgresSaver` for prod.

6. **Match models to nodes** — Use different models per node. Expensive reasoning models for orchestration and evaluation, cheap fast models for narrow sub-tasks.

## Reference Files

Read these for complete, copy-paste-ready code patterns:

- `references/orchestration-patterns.md` — StateGraph construction: linear, conditional, fan-out/fan-in, subgraph composition, adversarial evaluator loop
- `references/tool-calling-patterns.md` — Tool definitions, ToolNode wiring, programmatic sandbox execution, multi-shot examples
- `references/memory-state-patterns.md` — State schemas with reducers, checkpointing, context compaction, long-term vector store memory

## Common Mistakes to Avoid

- **Forgetting `add_messages` reducer** — Without it, each node's messages overwrite rather than append. Always use `Annotated[list, add_messages]` for chat history.
- **Not including a checkpointer with HITL** — `interrupt_before` silently fails without persistence. Always pair interrupts with a checkpointer.
- **Overloading the orchestrator's context** — Verbose tool outputs should be saved to files, not fed back into the main agent. Provide summaries + navigation tools instead.
- **Using `graph.invoke()` when streaming is better** — For long-running harnesses, use `graph.stream()` to get incremental updates and show progress.
- **Hardcoding model names** — Pass models as parameters so you can easily swap between tiers during development and A/B testing.
