# Tool Calling Patterns — LangChain Tools & ToolNode

Defining tools, wiring them into agents, and advanced patterns.

## Standard Tool Definition

Define tools with the `@tool` decorator — LangChain auto-generates the JSON schema for the LLM.

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Simple tool with docstring-based schema
@tool
def search_knowledge_base(query: str) -> str:
    """Search the internal knowledge base for relevant documents.
    Use this when the user asks about company policies or procedures."""
    results = vector_store.similarity_search(query, k=5)
    return "\n".join([doc.page_content for doc in results])

# Structured input tool with Pydantic schema
class RiskAssessmentInput(BaseModel):
    clause_text: str = Field(description="The contract clause to assess")
    risk_category: str = Field(description="One of: financial, legal, operational")
    severity_threshold: float = Field(default=0.7, description="Min severity to flag")

@tool(args_schema=RiskAssessmentInput)
def assess_risk(clause_text: str, risk_category: str, severity_threshold: float) -> dict:
    """Assess risk level of a contract clause against company policy."""
    return {"risk_level": "high", "score": 0.85, "flags": [...]}
```

## ToolNode Agent Loop in LangGraph

The standard ReAct loop: model calls tools → ToolNode executes → results fed back to model.

```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END, MessagesState

# 1. Define your tools
tools = [search_knowledge_base, assess_risk]

# 2. Bind tools to the model
model = ChatAnthropic(model="claude-sonnet-4-20250514")
model_with_tools = model.bind_tools(tools)

# 3. Agent node — calls the model
def agent(state: MessagesState) -> dict:
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# 4. Build the agent loop
builder = StateGraph(MessagesState)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))  # Auto-executes tool calls

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    tools_condition,  # Routes to "tools" if tool calls present, else END
)
builder.add_edge("tools", "agent")  # Loop back after tool execution

agent_graph = builder.compile()
```

## Programmatic Tool Calling (Sandbox Pattern)

For batch operations — the agent writes a script, a sandbox executes it, and a tool bridge handles authentication.

```python
@tool
def execute_in_sandbox(script: str) -> str:
    """Execute a Python script in an isolated sandbox.
    The script has access to `tool_bridge` for authenticated API calls.
    Use this for batch processing, loops, or aggregations."""
    import subprocess
    result = subprocess.run(
        ["docker", "exec", SANDBOX_CONTAINER, "python", "-c", script],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        return f"Error:\n{result.stderr}"
    return result.stdout
```

### Tool Bridge (Host-side REST API)

The sandbox can't access external APIs directly. Instead, it calls back to the host via an authenticated bridge.

```python
from fastapi import FastAPI, Depends

app = FastAPI()

@app.post("/tool/{tool_name}")
async def tool_bridge(tool_name: str, params: dict, session=Depends(verify_session)):
    """Authenticated bridge — sandbox calls this to invoke host tools."""
    tool_fn = TOOL_REGISTRY[tool_name]
    return await tool_fn(**params)
```

**Security considerations:**
- Session-ID authentication — sandbox gets a unique session token per run
- No direct internet access from the sandbox
- Locked-down endpoints — only registered tools are callable
- Timeout enforcement — kill long-running scripts

## Tool Use Examples (Multi-shot Prompting)

When the agent sends wrong parameter values, provide examples of correct usage.

```python
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

tool_use_examples = [
    HumanMessage(content="Find contracts expiring this quarter"),
    AIMessage(
        content="",
        tool_calls=[{
            "name": "search_knowledge_base",
            "args": {"query": "contracts expiring Q1 2026"},
            "id": "example_1"
        }]
    ),
    ToolMessage(content="Found 3 contracts...", tool_call_id="example_1"),
    AIMessage(content="I found 3 contracts expiring this quarter: ..."),
]

# Inject examples at the start of messages
def agent_with_examples(state: MessagesState) -> dict:
    messages = tool_use_examples + state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}
```

## Tool Selection Guide

| Pattern | When to use | Complexity |
|---|---|---|
| Standard `@tool` | Few tools, simple sequential tasks | Low |
| Pydantic `args_schema` | Complex inputs that need validation | Low-Medium |
| ToolNode agent loop | Standard ReAct pattern — model decides when/how to use tools | Medium |
| Tool Search / deferred loading | Many tools/MCPs, agent rarely needs all at once | Medium |
| Programmatic sandbox | Batch processing, loops, aggregations across many entities | High |
| Multi-shot examples | Agent misuses parameters despite good docstrings | Low (additive) |

**Layering tip:** You can combine patterns. A common production setup is: ToolNode for interactive tools + programmatic sandbox for batch operations + multi-shot examples for the tools the agent struggles with.
