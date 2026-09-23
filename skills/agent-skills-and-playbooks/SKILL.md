---
name: agent-skills-and-playbooks
description: Design and implement the two knowledge layers for agent harnesses — Skills (procedural markdown injected into prompts) and Playbooks (RAG-based reference documents retrieved at specific harness phases). Use this skill whenever the user wants to create agent skill files, build a RAG knowledge base for an agent, design a playbook retrieval pipeline, choose chunking strategies or embedding models, set up vector stores for agent memory or knowledge, implement hybrid search (vector + keyword), map document retrieval to specific workflow phases, evaluate retrieval quality with RAGAS, or decide whether domain knowledge should be a skill or a playbook. Trigger on mentions of "agent skills", "playbooks", "knowledge base", "RAG pipeline", "chunking strategy", "embedding model", "vector store", "hybrid search", "retrieval pipeline", "document retrieval", "knowledge grounding", "domain knowledge for agents", or any request to give an agent access to reference documents, SOPs, policies, or procedural instructions.
---

# Agent Skills & Playbooks

A skill for designing and implementing the two complementary knowledge layers that ground agents in domain expertise: **Skills** (procedural instructions injected into prompts) and **Playbooks** (reference documents retrieved via RAG).

## Why Two Layers?

Agents need two kinds of knowledge to perform well on domain-specific tasks:

1. **How to do the task** — step-by-step procedures, output formats, decision rules. These are small, deterministic, and must apply every time.
2. **What to check against** — company policies, legal precedents, SOPs, past examples, domain guides. These are large, contextual, and only relevant portions are needed per run.

Skills handle the first. Playbooks handle the second. Trying to use one for both leads to either bloated prompts (stuffing everything into skills) or unreliable procedure adherence (relying on RAG to retrieve procedural steps).

## Quick Decision Guide

| Question | If yes → | If no → |
|---|---|---|
| Must this happen every single run? | **Skill** | Consider playbook |
| Is it small enough to fit in a system prompt? | **Skill** | **Playbook** (RAG) |
| Is it procedural (how-to instructions)? | **Skill** | **Playbook** |
| Is it reference material (policies, precedents)? | **Playbook** | Consider skill |
| Does the agent need different subsets per run? | **Playbook** | Could be either |
| Does retrieval quality need measuring? | **Playbook** (RAGAS) | Skill (prompt adherence) |

## Detailed Comparison

| Aspect | Skills | Playbooks / Knowledge Base |
|---|---|---|
| What it contains | Procedural instructions — *how* to do the task | Reference material — *what* to check against |
| Delivery method | Injected directly into system prompt or tool definitions | Retrieved via RAG at a specific harness phase |
| Size | Small (fits in prompt — typically < 2K tokens) | Large (entire document corpus — thousands of docs) |
| Example | "Always extract clauses in this JSON schema" | "Company's negotiation playbook + past contract precedents" |
| Reliability mechanism | Prompt adherence (probabilistic) | Retrieval quality (measurable via RAGAS) |
| When to use | Codify repeatable procedures | Ground the agent in domain knowledge it wasn't trained on |
| Evaluation | Manual review, output format checks | RAGAS metrics: faithfulness, context precision/recall |

## Part 1: Agent Skills

Read `references/authoring-skills.md` for the complete guide to writing effective agent skills.

### What Makes a Good Skill

A skill is a self-contained markdown file that tells the agent *how* to do something. It gets injected into the system prompt (or a tool definition), so it must be concise and procedural.

Good skills are:
- **Specific** — clear step-by-step instructions, not vague guidance
- **Compact** — fits comfortably in a system prompt (< 2K tokens ideal)
- **Deterministic** — the same input should produce the same procedural steps
- **Testable** — you can verify whether the agent followed the skill
- **Self-contained** — doesn't depend on external retrieval to work

### Skill Scoping in Multi-Agent Harnesses

Different agents in a harness should receive different skills:

| Agent | Skills it receives | Why |
|---|---|---|
| Orchestrator | Routing logic, delegation rules, state management procedures | Keeps the orchestrator lean and focused |
| Sub-agents | Task-specific procedures, output format schemas | Each sub-agent is a specialist |
| Evaluator | Grading criteria, evaluation rubrics | Evaluator needs different knowledge than generators |

Never load all skills into every agent. Each agent should only see the skills relevant to its role — this protects context and improves adherence.

### When Skills Aren't Enough

Skills break down when:
- The knowledge corpus is too large to fit in a prompt
- Different runs need different subsets of knowledge
- The knowledge changes frequently (easier to update a document store than edit prompts)
- You need to measure retrieval quality

In these cases, use playbooks (RAG).

## Part 2: Playbooks / Knowledge Base (RAG)

Read `references/building-rag-pipeline.md` for the complete end-to-end implementation guide.

### What Goes in a Playbook

A playbook is a curated collection of reference documents that agents retrieve via RAG during specific harness phases. Typical contents:

- Company SOPs and procedures
- Legal precedents and case law
- Compliance policies and regulations
- Style guides and brand guidelines
- Past examples and templates
- Domain-specific reference materials
- FAQ documents and troubleshooting guides

### The RAG Pipeline — Components

Building a playbook retrieval system involves five decisions:

1. **Document ingestion** — How do you load and prepare documents? (LangChain document loaders)
2. **Chunking strategy** — How do you split documents into retrievable units? (Size, overlap, splitter type)
3. **Embedding model** — How do you convert chunks to vectors? (Model selection)
4. **Vector store** — Where do you store and search embeddings? (Database selection)
5. **Retrieval method** — How do you find relevant chunks at query time? (Similarity search, hybrid search, reranking)

Read `references/building-rag-pipeline.md` for implementation details on each component.

### Mapping Retrieval to Harness Phases

This is the key design decision: *when* in the harness workflow does retrieval happen?

Retrieval should be triggered at the phase where the agent needs domain context — not at the start (wastes context on potentially irrelevant documents) and not at the end (too late to influence analysis).

**Example — Contract Review Harness (8 phases):**

| Phase | Retrieval? | Why |
|---|---|---|
| 1. Text Extraction | No | Mechanical task, no domain knowledge needed |
| 2. Classification | No | Model's built-in knowledge is sufficient |
| 3. Clarifying Questions | No | Gathering user input |
| **4. Playbook Loading** | **Yes** | Retrieve SOPs, precedents, policies relevant to the classified contract type |
| 5. Clause Extraction | No | Skill-driven (extraction schema is a skill, not a playbook) |
| **6. Risk Analysis** | **Yes** | Each sub-agent gets relevant playbook chunks alongside the risk assessment skill |
| 7. Red Line Generation | No | Uses analysis results, not raw playbooks |
| 8. Executive Summary | No | Programmatic generation from templates |

**Key pattern:** Retrieval happens *after* classification (so you can filter by document type) and *before* analysis (so the agent has domain context for its work).

### Evaluating Retrieval Quality with RAGAS

Playbook retrieval quality is measurable — unlike skill adherence, which is probabilistic. Use RAGAS metrics:

| Metric | What it measures | What to do if low |
|---|---|---|
| **Context precision** | Are retrieved docs relevant? | Improve embedding model, tune chunking, add metadata filtering |
| **Context recall** | Were all relevant docs retrieved? | Increase k, improve overlap, check corpus completeness |
| **Faithfulness** | Is the answer grounded in retrieved context? | Strengthen grounding instructions in system prompt |
| **Answer relevancy** | Does the answer address the question? | Improve query formulation, add query expansion |

Read `references/building-rag-pipeline.md` for RAGAS integration code.

## Part 3: Skills + Playbooks Working Together

The most effective harnesses use both layers. Skills define *how* to do each task. Playbooks provide the domain knowledge to do it *well*.

### Worked Example: Contract Review

In the 8-phase contract review harness:

**Phase 4 — Playbook Loading:**
```
Query: "SOPs and precedents for {contract_type} contracts"
→ Retrieves: company negotiation playbook, past similar contracts, relevant policies
→ Loaded into: state["playbook_context"]
```

**Phase 5 — Clause Extraction (Skill-driven):**
```
Skill: "Extract all clauses using this JSON schema: {schema}. 
        For each clause, identify: type, parties, obligations, dates, penalties."
→ Skill defines the extraction procedure
→ No playbook needed — this is pure procedure
```

**Phase 6 — Risk Analysis (Skill + Playbook):**
```
Each sub-agent receives:
  - Skill: "Assess risk on a 1-5 scale using these criteria: {criteria}. 
            Compare clause terms against company policy. Flag deviations."
  - Playbook chunks: Relevant sections from company risk policy, past precedents
→ Skill tells the agent HOW to assess risk
→ Playbook tells the agent WHAT the company's standards are
```

### System Prompt Assembly Pattern

```python
def build_sub_agent_prompt(skill_path: str, playbook_chunks: list[str]) -> str:
    """Assemble a sub-agent's system prompt from skill + playbook."""
    # Load the skill (procedural instructions)
    with open(skill_path) as f:
        skill_content = f.read()
    
    # Format playbook context (retrieved documents)
    playbook_context = "\n---\n".join(playbook_chunks)
    
    return f"""You are a specialist agent performing a specific task.

## Your Procedure (follow these steps exactly)
{skill_content}

## Reference Material (use this to inform your analysis)
{playbook_context}

Always ground your analysis in the reference material above. 
If the reference material doesn't cover a topic, say so explicitly."""
```

## Reference Files

- `references/authoring-skills.md` — How to write effective agent skills: structure, best practices, templates, and examples
- `references/building-rag-pipeline.md` — End-to-end RAG pipeline: document loading, chunking strategies, embedding models, vector stores, hybrid search, RAGAS evaluation
