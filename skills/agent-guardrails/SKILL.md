---
name: agent-guardrails
description: Implement runtime controls (guardrails) for agent harnesses using LangChain Middleware + NeMo Guardrails + Guardrails AI. Use this skill whenever the user wants to add safety controls to an agent, implement input validation or output moderation, detect PII or prompt injection, add human-in-the-loop approval gates, enforce business rules on tool calls, set up topic control or jailbreak prevention, validate structured output, add toxicity or competitor mention filtering, implement symbolic guardrails for tool interception, or design a layered guardrails pipeline. Trigger on mentions of "guardrails", "safety controls", "input validation", "output moderation", "PII detection", "prompt injection", "jailbreak prevention", "HITL gates", "human approval", "content moderation", "NeMo Guardrails", "Guardrails AI", "LangChain middleware", "before_agent", "after_agent", "topic control", "business rules", or any request to make an agent safer or more controlled at runtime. This skill covers RUNTIME controls — for build-time evaluation and testing, use the agent-eval-pipeline skill instead.
---

# Agent Guardrails

Best-practice patterns for implementing runtime controls in agent harnesses using the recommended stack: **LangChain Middleware** (custom logic + HITL) + **NeMo Guardrails** (dialogue control + safety) + **Guardrails AI** (output validation).

## Why Guardrails Matter

Evaluation tells you the harness works during development. Guardrails keep it safe in production. They're the deterministic controls that run on every request — blocking dangerous inputs, validating tool parameters, and moderating outputs before users see them.

Without guardrails, your agent is one creative prompt injection away from doing something you didn't intend.

## The Three Guardrail Layers

Every harness should have controls at three points in the execution pipeline:

```
Input → [Pre-processing] → Agent → [In-processing / Tool-level] → Sub-agents → [Post-processing] → Output
```

| Layer | When it runs | What it does | Implementation |
|---|---|---|---|
| **Pre-processing** | Before the agent processes anything | Block banned keywords, detect prompt injection, anonymise PII, validate format, rate limit | LangChain `@before_agent` hooks — zero LLM cost for blocked requests |
| **In-processing** | During execution, before tool calls | Validate tool parameters, enforce business rules, require HITL approval for high-stakes tools | LangGraph conditional edges + `interrupt_before`. Symbolic guardrails. |
| **Post-processing** | After response, before user sees it | Content moderation, toxicity check, hallucination check, compliance scan, format validation | LangChain `@after_agent` hooks — use a cheap model as safety judge |

**Key principle:** Deterministic checks first (cheap, fast, zero LLM cost), model-based checks second (expensive, nuanced). Don't burn tokens on an LLM safety judge when a regex could have caught the problem.

## The Three Libraries — When to Use Each

| Library | Best for | Integration |
|---|---|---|
| **LangChain Middleware** | Custom business logic, PII regex, banned keywords, HITL approval gates | Native — `@before_agent` / `@after_agent` decorators |
| **NeMo Guardrails** | Programmable dialogue rails, topic control, jailbreak prevention, fact-checking | `RunnableRails` wraps any LangChain chain or LangGraph agent |
| **Guardrails AI** | Output validation with pre-built validators (competitor check, toxicity, PII scrub, structured output) | `guard.to_runnable()` for LCEL pipeline integration |

These complement each other. Use all three layered together for production harnesses.

## Implementation Guide

### Step 1: Design Your Guardrail Strategy

Before writing code, decide what controls you need at each layer:

**Pre-processing (input):**
- What inputs should be blocked outright? (prompt injection patterns, banned keywords)
- Should PII be detected and anonymised? (SSNs, emails, phone numbers)
- Are there rate limits or authentication requirements?

**In-processing (tool-level):**
- Which tools are high-stakes and need HITL approval? (external APIs, data mutations, publishing)
- Are there business rules that must be enforced? (transfer limits, approved accounts, role-based access)
- Should any tool parameters be validated before execution?

**Post-processing (output):**
- Should outputs be checked for toxicity or harmful content?
- Are competitor mentions forbidden?
- Must outputs conform to a specific format (JSON schema, required fields)?
- Should a hallucination check run against retrieved context?

### Step 2: Implement Pre-processing with LangChain Middleware

Read `references/langchain-middleware.md` for the complete code patterns.

Start with deterministic checks (zero LLM cost):
- Banned keyword filter for prompt injection patterns
- PII detection with regex (SSN, email, phone patterns)
- Input length / rate limiting

### Step 3: Add Topic Control with NeMo Guardrails

Read `references/nemo-guardrails.md` for Colang rail definitions and `RunnableRails` wrapping.

Use NeMo for:
- Topic steering (keep the agent on-task, refuse off-topic requests)
- Jailbreak detection rails
- Competitor discussion refusal
- Fact-checking rails

### Step 4: Add Output Validation with Guardrails AI

Read `references/guardrails-ai.md` for validator hub patterns and LCEL integration.

Use Guardrails AI for:
- Competitor mention scrubbing
- Toxicity detection
- PII scrubbing from outputs
- Structured output validation (ensure JSON schema compliance)

### Step 5: Wire HITL Gates in LangGraph

For high-stakes tool calls, use LangGraph's `interrupt_before` to pause execution and require human approval. This requires a checkpointer.

Read `references/langchain-middleware.md` for the symbolic guardrails and HITL patterns.

### Step 6: Monitor Guardrail Triggers

**Critical:** Without observability, you won't know when guardrails are helping vs. hurting.

- Trace every blocked/modified request in LangSmith
- Track false positive rate — aim for < 2% on legitimate inputs
- Review guardrail trigger patterns weekly to tune thresholds
- High false positive rates erode user trust faster than occasional misses

## The Recommended Layered Pipeline

```
Input
  │
  ├─ [1] LangChain Middleware @before_agent
  │    └─ Banned keywords, PII regex, rate limiting (zero LLM cost)
  │
  ├─ [2] NeMo Guardrails (input rails)
  │    └─ Topic control, jailbreak detection (Colang rules)
  │
  ├─ [3] Agent / LangGraph execution
  │    ├─ LangGraph interrupt_before on sensitive tools (HITL)
  │    └─ Conditional edges with business rule validation
  │
  ├─ [4] Guardrails AI validators
  │    └─ Competitor check, toxicity, PII scrub, format validation
  │
  ├─ [5] LangChain Middleware @after_agent
  │    └─ Final safety judge (cheap model), compliance scan
  │
  └─ Output
```

Monitor all guardrail triggers in LangSmith traces.

## Key Principles

1. **Deterministic first, model-based second** — Rule-based input filters are cheap and fast. Save LLM-based safety judges for the output stage where nuance matters.

2. **Human-in-the-loop requires a checkpointer** — Use `InMemorySaver` for dev, `PostgresSaver` for production. Without persistence, agents can't resume after human decisions.

3. **Monitor guardrail triggers in LangSmith** — Without observability, you're flying blind. Track what gets blocked, what gets modified, and your false positive rate.

4. **Symbolic guardrails at the tool level** — Use hook-based interception (before-tool-call) to enforce business rules that LLMs cannot bypass. The validation happens before execution — invalid operations never occur.

5. **Layer, don't replace** — Each library handles different concerns. LangChain Middleware for custom logic, NeMo for dialogue control, Guardrails AI for output validation. Use all three.

## Reference Files

Read these for complete, copy-paste-ready code patterns:

- `references/langchain-middleware.md` — Pre/post-processing hooks, PII detection, banned keywords, HITL gates, symbolic tool interception
- `references/nemo-guardrails.md` — Colang rail definitions, topic control, jailbreak prevention, RunnableRails wrapping
- `references/guardrails-ai.md` — Validator hub, competitor check, toxicity, PII scrub, structured output validation, LCEL integration
