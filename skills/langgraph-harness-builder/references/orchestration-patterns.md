# Orchestration Patterns — LangGraph StateGraph

Complete, copy-paste-ready Python patterns for building agent harness graphs.

## Minimal Linear Graph

A simple multi-phase pipeline. Each node runs sequentially.

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 1. Define typed state — the data contract between nodes
class HarnessState(TypedDict):
    messages: Annotated[list, add_messages]
    phase: str
    extracted_data: dict
    analysis: dict
    final_output: str

# 2. Define node functions — each receives and returns state
def extract(state: HarnessState) -> dict:
    """Phase 1: Extract structured data from input."""
    # Your extraction logic here (LLM call, parsing, etc.)
    return {"extracted_data": {...}, "phase": "extract_complete"}

def analyse(state: HarnessState) -> dict:
    """Phase 2: Analyse extracted data."""
    data = state["extracted_data"]
    return {"analysis": {...}, "phase": "analyse_complete"}

def generate(state: HarnessState) -> dict:
    """Phase 3: Generate final output from analysis."""
    return {"final_output": "...", "phase": "complete"}

# 3. Build the graph
builder = StateGraph(HarnessState)
builder.add_node("extract", extract)
builder.add_node("analyse", analyse)
builder.add_node("generate", generate)

# 4. Wire edges — linear pipeline
builder.add_edge(START, "extract")
builder.add_edge("extract", "analyse")
builder.add_edge("analyse", "generate")
builder.add_edge("generate", END)

# 5. Compile and run
graph = builder.compile()
result = graph.invoke({"messages": [], "phase": "init"})
```

## Conditional Routing (Branching)

Route to different nodes based on state values.

```python
from langgraph.graph import StateGraph, START, END

def route_by_classification(state: HarnessState) -> str:
    """Router function — returns the name of the next node."""
    doc_type = state["extracted_data"].get("type")
    if doc_type == "contract":
        return "contract_analyser"
    elif doc_type == "invoice":
        return "invoice_processor"
    else:
        return "general_analyser"

# Add conditional edges after the classify node
builder.add_conditional_edges(
    "classify",                    # Source node
    route_by_classification,       # Router function
    {                              # Map return values → node names
        "contract_analyser": "contract_analyser",
        "invoice_processor": "invoice_processor",
        "general_analyser": "general_analyser",
    }
)
```

## Parallel Sub-agents with Fan-out / Fan-in

Process multiple items concurrently using LangGraph's `Send` API.

```python
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END

def fan_out_clauses(state: HarnessState) -> list[Send]:
    """Fan out — spawn one sub-agent per clause."""
    clauses = state["extracted_data"]["clauses"]
    return [
        Send("analyse_clause", {"clause": c, "clause_id": i})
        for i, c in enumerate(clauses)
    ]

def analyse_clause(state: dict) -> dict:
    """Sub-agent: analyse a single clause."""
    clause = state["clause"]
    # LLM call to assess risk, extract terms, etc.
    return {"clause_result": {...}}

def fan_in_results(state: HarnessState) -> dict:
    """Fan in — aggregate all clause results."""
    # Results from parallel nodes are collected in state
    return {"analysis": {"aggregated": True, ...}}

builder.add_conditional_edges("extract", fan_out_clauses)
builder.add_node("analyse_clause", analyse_clause)
builder.add_edge("analyse_clause", "aggregate")
builder.add_node("aggregate", fan_in_results)
```

## Subgraph Composition (Hierarchical)

Embed a compiled subgraph as a node in a parent graph. Use this for reusable sub-workflows.

```python
# Build a reusable sub-harness
sub_builder = StateGraph(SubState)
sub_builder.add_node("step_a", step_a)
sub_builder.add_node("step_b", step_b)
sub_builder.add_edge(START, "step_a")
sub_builder.add_edge("step_a", "step_b")
sub_builder.add_edge("step_b", END)
sub_graph = sub_builder.compile()

# Embed in parent graph as a node
parent_builder = StateGraph(ParentState)
parent_builder.add_node("orchestrator", orchestrator)
parent_builder.add_node("sub_harness", sub_graph)  # Subgraph as node
parent_builder.add_node("finalise", finalise)
parent_builder.add_edge(START, "orchestrator")
parent_builder.add_edge("orchestrator", "sub_harness")
parent_builder.add_edge("sub_harness", "finalise")
parent_builder.add_edge("finalise", END)
parent_graph = parent_builder.compile()
```

## Adversarial Evaluator Loop (Generator + Evaluator)

The GAN-inspired quality loop — generator creates, evaluator grades, retry until criteria met or max iterations reached.

```python
import json
from langgraph.graph import StateGraph, START, END

MAX_ITERATIONS = 3

def generator(state: HarnessState) -> dict:
    """Generate or revise output based on feedback."""
    feedback = state.get("eval_feedback", "")
    prompt = f"Task: {state['task']}\nPrevious feedback: {feedback}\nGenerate improved output."
    response = generator_model.invoke(prompt)
    return {
        "draft": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }

def evaluator(state: HarnessState) -> dict:
    """Grade the draft against criteria. Uses a different (stronger) model."""
    prompt = f"""Grade this output on a 1-10 scale for each criterion:
    - Accuracy: {state['draft'][:500]}
    - Completeness: Are all required sections present?
    - Actionability: Are recommendations specific and actionable?
    Respond with JSON: {{"scores": {{}}, "passed": bool, "feedback": str}}"""
    eval_result = evaluator_model.invoke(prompt)
    parsed = json.loads(eval_result.content)
    return {
        "eval_scores": parsed["scores"],
        "eval_passed": parsed["passed"],
        "eval_feedback": parsed["feedback"],
    }

def should_retry(state: HarnessState) -> str:
    """Conditional edge — retry or finalise."""
    if state["eval_passed"] or state["iteration_count"] >= MAX_ITERATIONS:
        return "finalise"
    return "generator"  # Loop back for revision

builder = StateGraph(HarnessState)
builder.add_node("generator", generator)
builder.add_node("evaluator", evaluator)
builder.add_node("finalise", finalise)
builder.add_edge(START, "generator")
builder.add_edge("generator", "evaluator")
builder.add_conditional_edges("evaluator", should_retry)
builder.add_edge("finalise", END)
```

**Tips for effective adversarial evaluation:**
- Use a stronger model for the evaluator than the generator
- Weight criteria toward the model's weaknesses (score harder on what it struggles with)
- Let the evaluator interact with output when possible (e.g., Playwright MCP for web UIs)
- Define a "contract" (definition of done) upfront to prevent moving goalposts
- Cap iterations (3-5 is typical) to avoid infinite loops

## Human-in-the-Loop with Interrupt

Pause execution for human review. Requires a checkpointer.

```python
from langgraph.types import Command, interrupt
from langgraph.checkpoint.sqlite import SqliteSaver

def sensitive_action(state: HarnessState) -> dict:
    """Pauses for human approval before executing."""
    action = state["pending_action"]
    human_decision = interrupt(
        f"Approve this action? {action}\nRespond 'yes' or 'no'"
    )
    if human_decision.lower() == "yes":
        result = execute_action(action)
        return {"action_result": result}
    else:
        return {"action_result": "Action rejected by human reviewer"}

# Compile with checkpointer (required for interrupt/resume)
with SqliteSaver.from_conn_string("checkpoints.db") as cp:
    graph = builder.compile(
        checkpointer=cp,
        interrupt_before=["sensitive_action"],
    )
    config = {"configurable": {"thread_id": "run-42"}}
    result = graph.invoke(initial_state, config)
    # Graph is now paused — human reviews...
    graph.invoke(Command(resume="yes"), config)
```
