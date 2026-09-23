# Context Management Strategies

How to keep agents effective as their context windows fill. This is the most impactful memory design decision for long-running harnesses.

## The Problem: Context Anxiety

As the context window fills, models change their behaviour:
- They rush through steps
- They wrap up prematurely
- They declare things done when they're not
- They lose track of early instructions

This is not a bug — it's a fundamental property of how attention mechanisms work. Earlier content gets less attention as the window fills with newer content.

**Anthropic's findings:** Sonnet 4.5 showed significant context anxiety. Opus 4.5 was better. Opus 4.6 (1M context window) mostly eliminated the need for context resets — but context compaction was still necessary. Even with large windows, compaction improves quality by keeping the context focused.

## Strategy 1: Token-Based Trimming

Keep the most recent N tokens, drop the oldest messages. The simplest approach.

```python
from langchain_core.messages import trim_messages
from langchain_anthropic import ChatAnthropic

trimmer = trim_messages(
    max_tokens=8000,
    strategy="last",           # Keep most recent messages
    token_counter=ChatAnthropic(model="claude-sonnet-4-20250514"),
    include_system=True,       # Always keep the system prompt
    start_on="human",          # Ensure we start on a human turn
)

def agent_with_trimming(state: MessagesState) -> dict:
    trimmed = trimmer.invoke(state["messages"])
    response = model.invoke(trimmed)
    return {"messages": [response]}
```

**When to use:** Moderate conversations (< 100 messages) where old messages are genuinely irrelevant. Good for interactive agents where the recent exchange is what matters.

**Trade-off:** Old context is permanently lost from the agent's view. If an important early instruction gets trimmed, the agent won't follow it.

**Mitigation:** Always set `include_system=True` to preserve the system prompt. For critical instructions, put them in the system prompt rather than early user messages.

## Strategy 2: Summarise and Reset

Compress the full conversation history into a concise summary, then start fresh with only the summary and the most recent messages.

```python
from langchain_core.messages import SystemMessage

COMPACTION_THRESHOLD = 50  # messages

def maybe_compact_context(state: HarnessState) -> dict:
    """Summarise and reset when context gets too long."""
    messages = state["messages"]
    
    if len(messages) <= COMPACTION_THRESHOLD:
        return {}  # No compaction needed
    
    # Summarise everything except the last few messages
    history_to_summarise = messages[:-5]
    recent_messages = messages[-5:]
    
    summary_prompt = (
        "Summarise this conversation history concisely. "
        "Include: key decisions made, current task state, "
        "any important context the agent needs to continue. "
        "Be specific about data, numbers, and names."
    )
    
    summary = model.invoke([
        SystemMessage(content=summary_prompt),
        *history_to_summarise,
    ])
    
    return {
        "messages": [
            SystemMessage(content=f"Context summary from earlier in this session:\n{summary.content}"),
            *recent_messages,
        ]
    }
```

**When to use:** Very long single-session work (hours of continuous operation). When the agent needs to retain awareness of what it's done without carrying the full conversation.

**Trade-off:** The summary may lose important details. The summarising model might miss things that turn out to be important later.

**Mitigation:** Keep the last 5-10 messages uncompressed for continuity. Include explicit instructions in the summary prompt about what to preserve (decisions, data, state).

## Strategy 3: File-Based Offloading

Save verbose content to files. Keep only summaries in the context window. Give the agent tools to read file details on demand.

```python
@tool
def save_to_workspace(filename: str, content: str) -> str:
    """Save verbose content to the workspace filesystem.
    Returns a brief summary for your context window."""
    path = f"./workspace/{filename}"
    with open(path, "w") as f:
        f.write(content)
    
    lines = content.count("\n") + 1
    return (
        f"Saved to {path} ({lines} lines, {len(content)} chars). "
        f"Preview: {content[:300]}..."
    )

@tool
def read_workspace_file(filename: str) -> str:
    """Read full content from a workspace file when you need details."""
    path = f"./workspace/{filename}"
    with open(path) as f:
        return f.read()

@tool
def list_workspace_files() -> str:
    """List all files in the workspace with sizes."""
    import os
    files = []
    for f in os.listdir("./workspace"):
        size = os.path.getsize(f"./workspace/{f}")
        files.append(f"{f} ({size} bytes)")
    return "\n".join(files)
```

**When to use:** When tool outputs are verbose (API responses, search results, log files, data dumps). These flood the context window with content the agent rarely needs to re-read in full.

**Trade-off:** The agent must actively use the read tool to access details. If the prompt doesn't emphasise this, the agent may proceed without checking files.

**Mitigation:** Add clear instructions in the system prompt: "Verbose outputs are saved to workspace files. Always check the relevant file before making decisions that depend on detailed data."

## Strategy 4: Context Resets (Fresh Window)

Start each phase, sprint, or feature in a completely fresh context window. The new session reads a progress file to reconstruct what it needs.

```python
def start_new_sprint(sprint_number: int) -> dict:
    """Begin a fresh context window for a new sprint."""
    # Read progress from previous sprints
    progress = read_progress_file()
    
    # Read the harness spec (what we're building)
    with open("./workspace/harness_spec.md") as f:
        spec = f.read()
    
    # Construct a focused system prompt
    system_prompt = f"""You are continuing work on a harness project.

## Project Spec
{spec}

## Progress So Far
{json.dumps(progress, indent=2)}

## Your Task This Sprint
Complete feature: {progress['current_feature']['name']}

## Important Context from Previous Sprints
{progress['context_summary']}

Previous decisions:
{chr(10).join(progress['decisions_log'])}
"""
    
    return {"system_prompt": system_prompt, "messages": []}
```

**When to use:** Multi-sprint builds, the Initialiser/Coder pattern, or any task that spans multiple sessions by design. Also when a model shows severe context anxiety that compaction doesn't fix.

**Trade-off:** Requires maintaining a progress tracking file. If the file is incomplete or inaccurate, the new session starts with wrong assumptions.

**Mitigation:** Make progress file updates part of the harness process, not optional. Every sprint should end with an explicit "update progress" step.

## Choosing the Right Strategy

| Scenario | Strategy | Why |
|---|---|---|
| Chat agent with moderate conversations | Token trimming | Simple, recent context is most relevant |
| Long coding session (2-4 hours) | Summarise-and-reset | Maintains awareness while managing length |
| Agent with verbose API tools | File offloading | Keep context lean, details available on demand |
| Multi-day project build | Context resets + progress file | Each session starts fresh and focused |
| Production harness (many concurrent runs) | LangGraph checkpointing | Built-in state persistence and resume |

**You can combine strategies.** A common production pattern:
1. File offloading for verbose tool outputs (always active)
2. Token trimming for moderate growth (background compaction)
3. Summarise-and-reset when approaching limits (triggered by threshold)
4. Context resets between major phases (structural, by design)

## Monitoring Context Health

Track these in LangSmith to catch context problems early:

- **Total tokens per node** — Are any nodes consuming disproportionate context?
- **Messages per run** — Is the conversation growing unexpectedly?
- **Output quality over time** — Does quality degrade as context fills? (Run evals at different context lengths)
- **Premature completion rate** — How often does the agent declare "done" before the task is actually complete?
