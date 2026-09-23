# Handoff Patterns — Progress Tracking & Sprint-Based Memory

How agents hand off work to each other or to future sessions of themselves, maintaining continuity without carrying the full conversation history.

## The Initialiser/Coder Pattern

The foundational handoff pattern, established by Anthropic for long-running coding tasks.

### How It Works

1. **Initialiser agent** runs first:
   - Reads the project spec / user request
   - Sets up the environment (directory structure, dependencies)
   - Breaks the project into discrete features
   - Creates a progress tracking file
   - Terminates

2. **Coder agent** runs in a loop:
   - Reads the progress tracking file
   - Picks up the next incomplete feature
   - Implements the feature
   - Runs tests / validation
   - Commits to git
   - Updates the progress file
   - Terminates (or continues to next feature if context allows)

### Implementation

```python
import json
from datetime import datetime

PROGRESS_FILE = "./workspace/progress.json"

def initialise_project(spec: str) -> dict:
    """Initialiser agent: break spec into features and create progress file."""
    # Use LLM to decompose the spec into features
    decomposition = planning_model.invoke(
        f"Break this project into discrete, independently implementable features. "
        f"Return as JSON array of {{id, name, description, dependencies}}.\n\n{spec}"
    )
    
    features = json.loads(decomposition.content)
    
    progress = {
        "project_name": "...",
        "created_at": datetime.now().isoformat(),
        "spec_summary": spec[:500],
        "features": [
            {**f, "status": "pending", "completed_at": None}
            for f in features
        ],
        "current_feature": features[0]["id"] if features else None,
        "context_summary": "",
        "decisions_log": [],
        "git_log": [],
    }
    
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)
    
    return progress

def read_progress() -> dict:
    """Read current progress state."""
    with open(PROGRESS_FILE) as f:
        return json.load(f)

def update_progress(
    feature_id: str,
    status: str,
    context_summary: str = None,
    decision: str = None,
    git_commit: str = None,
):
    """Update progress after completing work."""
    progress = read_progress()
    
    # Update feature status
    for f in progress["features"]:
        if f["id"] == feature_id:
            f["status"] = status
            if status == "complete":
                f["completed_at"] = datetime.now().isoformat()
    
    # Set next feature
    if status == "complete":
        remaining = [f for f in progress["features"] if f["status"] == "pending"]
        progress["current_feature"] = remaining[0]["id"] if remaining else None
    
    # Append context and decisions
    if context_summary:
        progress["context_summary"] = context_summary
    if decision:
        progress["decisions_log"].append(decision)
    if git_commit:
        progress["git_log"].append(git_commit)
    
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)
```

### Progress File Schema

```json
{
  "project_name": "string",
  "created_at": "ISO datetime",
  "spec_summary": "string — truncated project spec for quick reference",
  "features": [
    {
      "id": "F001",
      "name": "Feature name",
      "description": "What this feature does",
      "dependencies": ["F000"],
      "status": "pending | in_progress | complete | blocked",
      "completed_at": "ISO datetime | null",
      "notes": "Any implementation notes from the agent"
    }
  ],
  "current_feature": "F001 | null",
  "context_summary": "string — running summary of key context from previous sprints",
  "decisions_log": [
    "string — each significant decision with rationale"
  ],
  "git_log": [
    "string — commit messages for traceability"
  ]
}
```

## Sprint-Based Handoffs

For multi-sprint work, each sprint is a fresh context window. The "contract negotiation" pattern defines the scope of each sprint upfront.

### Sprint Planning

```python
def plan_sprints(features: list[dict], max_features_per_sprint: int = 3) -> list[dict]:
    """Group features into sprints based on dependencies and complexity."""
    sprints = []
    remaining = list(features)
    sprint_num = 1
    
    while remaining:
        # Pick features whose dependencies are all complete
        available = [
            f for f in remaining
            if all(
                dep in [c["id"] for s in sprints for c in s["features"]]
                for dep in f.get("dependencies", [])
            )
        ]
        
        sprint_features = available[:max_features_per_sprint]
        sprints.append({
            "sprint_number": sprint_num,
            "features": sprint_features,
            "definition_of_done": [
                f"Feature {f['id']} implemented and tested" for f in sprint_features
            ],
        })
        
        for f in sprint_features:
            remaining.remove(f)
        sprint_num += 1
    
    return sprints
```

### Sprint Execution with Context Reset

```python
def execute_sprint(sprint: dict) -> dict:
    """Execute a sprint with a fresh context window."""
    progress = read_progress()
    
    # Build focused system prompt from progress file
    system_prompt = f"""You are executing Sprint {sprint['sprint_number']}.

## Features to Complete This Sprint
{json.dumps(sprint['features'], indent=2)}

## Definition of Done
{chr(10).join(sprint['definition_of_done'])}

## Context from Previous Sprints
{progress['context_summary']}

## Key Decisions Made So Far
{chr(10).join(progress['decisions_log'][-10:])}

Complete each feature, run tests, and update progress when done.
"""
    
    # Run the agent with fresh context
    result = agent_graph.invoke({
        "messages": [SystemMessage(content=system_prompt)],
        "phase": "sprint_start",
    })
    
    return result
```

### Sprint Handoff Checklist

At the end of every sprint, before context resets:

1. **Update progress file** with completed features and status
2. **Write context summary** — what was done, key findings, blockers
3. **Log decisions** — any architectural or design choices made during the sprint
4. **Commit to git** — all code changes committed with descriptive messages
5. **Run tests** — verify nothing is broken before handoff
6. **Note blockers** — anything the next sprint needs to address

## Multi-Agent Memory Coordination

When multiple agents need to share memory within a single harness run.

### Shared State Pattern (LangGraph)

All agents share the same `State` object. Each agent reads from and writes to specific fields.

```python
class SharedHarnessState(TypedDict):
    # Shared by all agents
    messages: Annotated[list, add_messages]
    phase: str
    
    # Written by extractor, read by analyser
    extracted_data: dict
    
    # Written by analyser, read by generator
    analysis: dict
    
    # Written by each sub-agent, aggregated via reducer
    clause_results: Annotated[list, operator.add]
```

### File-Based Handoff Between Agents

When agents run in separate processes or need isolation, use workspace files.

```python
WORKSPACE = "./workspace"

def agent_a_output(result: dict):
    """Agent A saves its output for Agent B."""
    with open(f"{WORKSPACE}/agent_a_output.json", "w") as f:
        json.dump(result, f, indent=2)

def agent_b_input() -> dict:
    """Agent B reads Agent A's output."""
    with open(f"{WORKSPACE}/agent_a_output.json") as f:
        return json.load(f)
```

### Evaluator Handoff

The adversarial evaluator pattern requires specific handoff data:

```python
def generator_to_evaluator_handoff(state: HarnessState) -> dict:
    """Package the generator's output for the evaluator."""
    return {
        "draft": state["draft"],
        "iteration": state["iteration_count"],
        "task_spec": state["task"],
        "previous_feedback": state.get("eval_feedback", "First iteration"),
        # Don't pass the generator's full conversation —
        # evaluator needs a fresh perspective
    }
```

**Important:** The evaluator should NOT see the generator's internal reasoning. Give it only the output and the criteria. A fresh perspective is the whole point of adversarial evaluation.

## Common Pitfalls

1. **Over-detailed progress files** — Keep progress files concise. A 5,000-word progress file defeats the purpose of context resets. The summary should be < 500 words.

2. **No decisions log** — Without recording why decisions were made, the next sprint may undo or contradict earlier choices. Log every significant decision with its rationale.

3. **Stale context summaries** — The context summary should be rewritten (not appended to) at the end of each sprint. Old summaries accumulate irrelevant information.

4. **Missing dependency tracking** — If Sprint 3 depends on Sprint 2's output but Sprint 2 didn't save it properly, Sprint 3 fails. Test handoffs explicitly.

5. **Assuming all agents need all state** — Each agent should receive only the state fields it needs. An evaluator doesn't need the extraction data. An extractor doesn't need previous analysis results.
