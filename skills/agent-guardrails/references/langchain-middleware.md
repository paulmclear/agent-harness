# LangChain Middleware — Pre/Post Processing & HITL Gates

Zero-LLM-cost input guards, output validators, symbolic tool interception, and human approval gates.

## Pre-processing Hook (@before_agent)

Runs before the agent processes anything. Use for deterministic, zero-cost input filtering.

```python
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

def before_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    """Pre-processing guardrail — runs before the agent."""
    last_message = state["messages"][-1].content

    # 1. Banned keyword filter (deterministic, zero cost)
    banned = ["ignore previous instructions", "system prompt", "disregard above"]
    if any(kw in last_message.lower() for kw in banned):
        raise ValueError("Input blocked: potential prompt injection detected")

    # 2. PII detection (regex-based)
    import re
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"

    content = last_message
    content = re.sub(ssn_pattern, "[SSN REDACTED]", content)
    content = re.sub(email_pattern, "[EMAIL REDACTED]", content)
    content = re.sub(phone_pattern, "[PHONE REDACTED]", content)
    state["messages"][-1].content = content

    # 3. Input length check
    if len(last_message) > 50000:
        raise ValueError("Input too long — maximum 50,000 characters")

    return state
```

## Post-processing Hook (@after_agent)

Runs after the agent produces a response, before the user sees it. Use for content moderation and compliance.

```python
def after_agent(state: AgentState, config: RunnableConfig) -> AgentState:
    """Post-processing guardrail — runs after the agent."""
    output = state["messages"][-1].content

    # 1. Content moderation (use a cheap/fast model as safety judge)
    safety_check = safety_model.invoke(
        f"Is this response safe, appropriate, and free of harmful content? "
        f"Answer YES or NO with a brief reason: {output[:500]}"
    )
    if "NO" in safety_check.content.upper():
        state["messages"][-1].content = (
            "I'm unable to provide that response. Please rephrase your request."
        )

    # 2. Compliance scan (deterministic)
    forbidden_phrases = ["not financial advice", "guaranteed returns"]
    for phrase in forbidden_phrases:
        if phrase in output.lower():
            # Log to LangSmith for review
            log_guardrail_trigger("compliance", phrase, output)

    return state
```

## Wiring Middleware into an Agent

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=model,
    tools=tools,
    before_agent=before_agent,
    after_agent=after_agent,
)
```

## Symbolic Guardrails — Hook-based Tool Interception

Enforce business rules at the tool level that LLMs cannot bypass. The validation happens before execution — invalid operations never occur.

```python
def validate_before_tool_call(tool_name: str, params: dict) -> dict:
    """Hook-based interception — runs before any tool executes.
    Invalid operations never occur."""

    if tool_name == "transfer_funds":
        if params.get("amount", 0) > 10000:
            raise ValueError("Transfers > $10K require manager approval")
        if params.get("destination") not in APPROVED_ACCOUNTS:
            raise ValueError(f"Destination {params['destination']} not approved")

    if tool_name == "delete_record":
        # Always require human confirmation for destructive actions
        raise HumanApprovalRequired(
            f"Confirm deletion of record {params['record_id']}?"
        )

    if tool_name == "send_email":
        # Validate recipient domain
        recipient = params.get("to", "")
        allowed_domains = ["company.com", "partner.com"]
        domain = recipient.split("@")[-1] if "@" in recipient else ""
        if domain not in allowed_domains:
            raise ValueError(f"Cannot send to external domain: {domain}")

    return params  # Pass through if valid
```

### Wiring into ToolNode

```python
from langgraph.prebuilt import ToolNode

class GuardedToolNode(ToolNode):
    def invoke(self, state, config=None):
        for tool_call in state["messages"][-1].tool_calls:
            validate_before_tool_call(tool_call["name"], tool_call["args"])
        return super().invoke(state, config)
```

## Human-in-the-Loop Approval Gates

Pause execution for human review before high-stakes actions. Requires a checkpointer.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command, interrupt

def sensitive_tool_node(state: HarnessState) -> dict:
    """Tool node that requires human approval."""
    action = state["pending_action"]

    # Interrupt — graph pauses here, waiting for human input
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
        interrupt_before=["sensitive_tool_node"],
    )

    # Run until interruption
    config = {"configurable": {"thread_id": "run-42"}}
    result = graph.invoke(initial_state, config)
    # Graph is now paused...

    # Human reviews and resumes
    graph.invoke(Command(resume="yes"), config)
```

**Important:** Without a checkpointer, `interrupt_before` / `interrupt_after` silently fail. Always pair interrupts with persistence:
- Dev: `SqliteSaver` or `InMemorySaver`
- Production: `PostgresSaver`

## Guardrail Logging for LangSmith

Track every guardrail trigger so you can monitor false positive rates and tune thresholds.

```python
from langsmith import Client

client = Client()

def log_guardrail_trigger(
    guardrail_type: str,
    trigger_reason: str,
    content: str,
    action_taken: str = "blocked"
):
    """Log guardrail triggers to LangSmith for monitoring."""
    client.create_feedback(
        run_id=current_run_id,
        key=f"guardrail_{guardrail_type}",
        score=0.0,  # 0 = triggered
        comment=f"Reason: {trigger_reason} | Action: {action_taken}",
    )
```

Monitor in LangSmith:
- Filter traces by guardrail feedback keys
- Track trigger frequency over time
- Review blocked inputs to identify false positives
- Target < 2% false positive rate on legitimate inputs
