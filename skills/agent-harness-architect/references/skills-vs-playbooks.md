# Skills vs Playbooks — When to Use Which

Two complementary knowledge layers that ground agents in domain expertise.

## Agent Skills

Portable, self-contained units of domain knowledge and procedural logic — markdown files that tell the agent *how* to do something. Codified best practices.

- **What it contains:** Procedural instructions — *how* to do the task
- **Delivery method:** Injected directly into system prompt or tool definitions
- **Size:** Small (fits in prompt)
- **Example:** "Always extract clauses in this JSON schema"
- **Reliability mechanism:** Prompt adherence (probabilistic)
- **When to use:** Codify repeatable procedures that must happen every single time

**Rule of thumb:** If something must happen every single time, codify it as a skill. Skills expand capabilities for guided co-pilot interactions.

## Playbooks / Knowledge Base (RAG)

A curated collection of reference documents — SOPs, precedents, policies, templates, domain guides — that agents retrieve via RAG at the appropriate phase.

- **What it contains:** Reference material — *what* to check against
- **Delivery method:** Retrieved via RAG at a specific harness phase
- **Size:** Large (entire document corpus)
- **Example:** "Company's negotiation playbook + past contract precedents"
- **Reliability mechanism:** Retrieval quality (measurable via RAGAS)
- **When to use:** Ground the agent in domain-specific knowledge it wasn't trained on

## Comparison Table

| Aspect | Skills | Playbooks / Knowledge Base |
|---|---|---|
| What it contains | Procedural instructions | Reference material |
| Delivery method | Injected into system prompt | Retrieved via RAG |
| Size | Small (fits in prompt) | Large (document corpus) |
| Reliability | Prompt adherence | Retrieval quality (RAGAS) |
| When to use | Codify repeatable procedures | Ground in domain knowledge |

## Contract Review Demo Pattern (Worked Example)

In the 8-phase contract review harness, skills and playbooks work together:

1. **Phase 4 — Playbook Loading:** RAG query against knowledge base (SOPs, precedents, policies) relevant to the classified contract type
2. **Phase 5 — Clause Extraction:** Skill defines the extraction schema and procedure
3. **Phase 6 — Risk Analysis:** Each sub-agent receives both the skill (how to assess risk) and relevant playbook chunks (what the company's risk policy says)

## Playbook Design Checklist

When designing a playbook/knowledge base, specify:

- **Knowledge base contents:** What document types? (SOPs, legal precedents, compliance policies, style guides, past examples)
- **Retrieval method:** Vector store (which?), hybrid search, knowledge graph
- **Chunking strategy:** Chunk size, overlap, splitter type (RecursiveCharacterTextSplitter recommended)
- **Embedding model:** e.g. text-embedding-3-large, Cohere embed-v3
- **When loaded:** Which harness phase triggers retrieval?
- **Retrieval scope:** Which agents query the knowledge base? Orchestrator? Sub-agents?
- **Eval:** RAGAS metrics — context precision, context recall, faithfulness
