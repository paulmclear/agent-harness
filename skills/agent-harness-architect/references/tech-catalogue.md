# Technology & Tools Catalogue

Tools, frameworks, and technologies mapped to harness components.

## Preferred Stack

> **LangGraph + LangChain + LangSmith** is the default for all new harness projects unless there's a strong reason to deviate.

| Tool | Role in Harness | Maps to Concept |
|---|---|---|
| **LangGraph** | Orchestration engine — stateful, cyclical graphs | Architecture, State Management, Planning, Checkpointing |
| **LangChain** | Agent primitives — chains, tools, prompts, memory, model wrappers | Tool Calling, Memory, Skills/Prompts, Model flexibility |
| **LangSmith** | Observability & evaluation — tracing, debugging, eval datasets | Validation & Evaluation, Cost tracking, Assumptions review |

### How the Preferred Stack Maps to the 12 Harness Concepts

1. **Harness Architecture** → LangGraph's `StateGraph` defines topology. `add_node` for agents, `add_edge` / `add_conditional_edges` for flow.
2. **Planning** → Fixed plans = deterministic edges. Dynamic plans = LLM node that outputs next steps, fed back as state.
3. **File System** → LangChain document loaders + custom tools for workspace read/write.
4. **Task Delegation** → LangGraph subgraphs or separate compiled graphs invoked as tool calls. Different models per node.
5. **Tool Calling** → LangChain tool definitions + `ToolNode` in LangGraph. Human-approval nodes before high-stakes tools.
6. **Memory** → Short-term: LangGraph `State` via checkpointers. Long-term: LangChain vector stores or knowledge graphs.
7. **State Management** → LangGraph typed `State` with reducers, persisted via `SqliteSaver` / `PostgresSaver`.
8. **Code Execution** → Custom tool nodes wrapping sandbox execution (Docker / LLM Sandbox).
9. **Context Management** → Graph structure isolates context per node. Message trimming / summarisation in state reducers.
10. **Human in the Loop** → LangGraph `interrupt_before` / `interrupt_after`. Resume with `Command(resume=...)`.
11. **Validation Loops** → Cyclic edges: Generator → Evaluator → conditional edge back to Generator.
12. **Skills & Playbooks** → Skills = LangChain prompt templates as reusable modules. Playbooks = RAG via LangChain vector stores + retrievers.

## Agent Frameworks & SDKs

| Tool | Type | Notes |
|---|---|---|
| **LangGraph** ⭐ | Graph-based orchestration | Preferred. Stateful, cyclical graphs with checkpointing. |
| **LangChain** ⭐ | Agent primitives / SDK | Preferred. Chains, tools, prompts, memory, model wrappers. |
| **LangSmith** ⭐ | Observability & eval | Preferred. Tracing, debugging, eval datasets, cost tracking. |
| **LangChain Deep Agents** ⭐ | Research agent framework | For deep research and multi-step reasoning. |
| Claude Agent SDK | SDK | Anthropic's harness experiments; supports context compaction. |
| Claude Code | CLI Agent | General-purpose; Stripe's "minions" harness wraps this. |
| OpenAI Agents SDK | SDK | Guardrails, structured output, handoffs. |
| AutoGen | Multi-agent framework | Flexible agent communication patterns. |

## Tool Calling & Integration

| Tool | Maps to | Notes |
|---|---|---|
| MCP (Model Context Protocol) | Tool integration layer | Standardised API access; Host → Client → Server. |
| Tool Search (deferred loading) | Context management | Loads tool schemas on-demand. |
| Programmatic Tool Calling | Batch processing | Agent writes scripts; sandbox executes; tool bridge for auth. |
| LLM Sandbox | Code execution | Docker-based isolated execution. |
| Playwright MCP | Evaluator interaction | Navigate, screenshot, and test web UIs. |

## Memory & Knowledge

| Tool | Maps to | Notes |
|---|---|---|
| Vector databases (Pinecone, Weaviate, Chroma) | Long-term memory / RAG / Playbooks | Semantic search over knowledge and domain playbooks. |
| Knowledge graphs (e.g. Graffiti) | Long-term memory | Temporal graphs for evolving knowledge. |
| Markdown files | Short-term memory / Agent Skills | Read into system prompts; lightweight and portable. |
| Progress tracking files | State management | Initialiser/Coder pattern; each agent reads and updates. |
| LangChain document loaders + text splitters | Playbook ingestion | Load SOPs, policies, templates. Chunk with `RecursiveCharacterTextSplitter`. |
| Hybrid search (vector + keyword) | Playbook retrieval | Combine semantic similarity with BM25 for higher precision. |

## Evaluation & QA

| Tool | Maps to | Notes |
|---|---|---|
| **LangSmith Evaluations** ⭐ | Build-time + online eval | LLM-as-judge, heuristic, human annotation, pairwise comparison. |
| **RAGAS** ⭐ | RAG-specific evaluation | Reference-free RAG metrics. Integrates with LangSmith. |
| **DeepEval** ⭐ | CI/CD test runner | Pytest-native. 40+ red-teaming attacks. Regression testing. |
| Test suites (pytest, Jest) | Validation loops | Generate → test → fix; Stripe runs against 3M test suite. |
| Linters / type checkers | Ralph Wiggum Loop | Verifiable sources that can't lie; explicit stop conditions. |
| Adversarial evaluator pattern | Subjective QA | GAN-inspired: generator + evaluator in a loop. |

## Runtime Guardrails

| Library | Type | Integration | Best for |
|---|---|---|---|
| **LangChain Middleware** ⭐ | Built-in | Native `@before_agent` / `@after_agent` | Custom business logic, PII, HITL gates. |
| **NeMo Guardrails** ⭐ | Open-source | `RunnableRails` wraps LangChain chains | Dialogue rails, jailbreak prevention, fact-checking. |
| **Guardrails AI** ⭐ | Open-source | `guard.to_runnable()` for LCEL | Validator hub, competitor check, toxicity, structured output. |
| LLM Guard | Open-source | Custom integration | Input/output security scanning. |

## Models by Role

| Role | Recommended tier | Examples |
|---|---|---|
| Orchestrator / Supervisor | Top-tier reasoning | Opus 4.6, Gemini 2.5 Pro |
| Sub-agents (narrow tasks) | Fast / cheap | Gemini 2.5 Flash, Haiku, Sonnet |
| Evaluator / QA | Strong reasoning | Opus 4.6, Opus 4.5 |
| Planning / Spec expansion | Strong reasoning | Opus 4.6 |

## Planning & Spec Tools

| Tool | Maps to | Notes |
|---|---|---|
| BMAD | Spec-driven development | Structured requirements before dev begins. |
| SpecKit | Spec-driven development | Prevents under-scoping. |
| OpenSpec | Spec-driven development | Requirements framework. |
