# Long-Term Memory — Vector Stores, Knowledge Graphs, and Autonomous Agents

Persistent memory that survives across separate harness runs, enabling agents to learn from experience and recall past work.

## When You Need Long-Term Memory

Most harnesses don't need long-term memory. Working memory + file-based memory handles the vast majority of use cases. Add long-term memory when:

- The agent runs repeatedly on similar tasks and should improve over time
- Past run outcomes are relevant to current decisions
- The agent needs to avoid repeating mistakes from previous sessions
- The agent is autonomous (event-triggered) and must reconstruct context on each invocation

## Vector Store Memory

Store past interactions, outcomes, and learned insights as embeddings. Retrieve relevant memories via semantic search at the start of each run.

### Setup

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from datetime import datetime

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

memory_store = Chroma(
    collection_name="agent_memory",
    embedding_function=embeddings,
    persist_directory="./memory_db",
)
```

### Saving Memories After Each Run

```python
def save_run_memory(state: HarnessState):
    """Save a structured memory of this harness run."""
    memory_text = (
        f"Task: {state['task']}\n"
        f"Outcome: {state['final_output'][:500]}\n"
        f"Quality score: {state.get('eval_scores', 'N/A')}\n"
        f"Key decisions: {'; '.join(state.get('decisions', []))}\n"
        f"Lessons learned: {state.get('lessons', 'None noted')}"
    )
    
    memory_store.add_texts(
        texts=[memory_text],
        metadatas=[{
            "run_id": state["run_id"],
            "task_type": state.get("task_type", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "quality_score": state.get("eval_scores", {}).get("overall", 0),
            "success": state.get("eval_passed", False),
        }]
    )
```

### Recalling Relevant Memories

```python
def recall_relevant_memories(task: str, k: int = 5) -> str:
    """Retrieve memories relevant to the current task."""
    memories = memory_store.similarity_search(task, k=k)
    
    if not memories:
        return "No relevant past experiences found."
    
    formatted = []
    for i, mem in enumerate(memories, 1):
        formatted.append(
            f"Memory {i} ({mem.metadata.get('timestamp', 'unknown date')}):\n"
            f"{mem.page_content}"
        )
    
    return "\n---\n".join(formatted)
```

### Injecting Memories into Agent Context

```python
def build_agent_prompt_with_memory(task: str, base_prompt: str) -> str:
    """Build an agent prompt enriched with relevant past experiences."""
    memories = recall_relevant_memories(task)
    
    return f"""{base_prompt}

## Relevant Past Experiences
The following are memories from similar previous tasks. 
Use these to inform your approach — learn from past successes and avoid past mistakes.

{memories}
"""
```

### Memory Maintenance

Vector store memories accumulate over time. Maintain them:

```python
def prune_old_memories(days_threshold: int = 90):
    """Remove memories older than the threshold."""
    cutoff = (datetime.now() - timedelta(days=days_threshold)).isoformat()
    # Implementation depends on vector store — Chroma, Pinecone, etc.
    # have different deletion APIs

def consolidate_memories(task_type: str):
    """Merge similar memories into consolidated insights."""
    all_memories = memory_store.similarity_search(task_type, k=50)
    
    consolidation_prompt = (
        "Review these past experiences and distil them into "
        "3-5 key insights and best practices. Be specific."
    )
    
    insights = model.invoke([
        SystemMessage(content=consolidation_prompt),
        HumanMessage(content="\n---\n".join([m.page_content for m in all_memories])),
    ])
    
    # Replace many specific memories with consolidated insights
    # (implementation depends on your vector store's delete API)
    memory_store.add_texts(
        texts=[insights.content],
        metadatas=[{
            "type": "consolidated_insight",
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
            "source_count": len(all_memories),
        }]
    )
```

## Knowledge Graph Memory

For complex domains where relationships between entities matter more than raw text similarity.

### When to Use Knowledge Graphs Over Vector Stores

| Use case | Vector store | Knowledge graph |
|---|---|---|
| "Find similar past tasks" | Better (semantic similarity) | Possible but overkill |
| "What decisions affected outcome X?" | Weak (no causal links) | Better (explicit relationships) |
| "How has entity X changed over time?" | Weak (no temporal ordering) | Better (temporal graphs) |
| "What are all the dependencies of Y?" | Weak (no graph traversal) | Better (path queries) |

### Temporal Knowledge Graphs (e.g., Graffiti)

Temporal graphs track how knowledge evolves over time — entities and relationships have valid time ranges.

```python
# Conceptual pattern — specific implementation depends on the graph library
class AgentKnowledgeGraph:
    def __init__(self, graph_db):
        self.db = graph_db
    
    def record_observation(self, entity: str, attribute: str, value: str, timestamp: str):
        """Record a time-stamped observation."""
        self.db.add_edge(
            source=entity,
            target=value,
            relationship=attribute,
            valid_from=timestamp,
        )
    
    def query_current_state(self, entity: str) -> dict:
        """Get the current known state of an entity."""
        return self.db.query(
            f"MATCH (e {{name: '{entity}'}})-[r]->(v) "
            f"WHERE r.valid_to IS NULL "  # Still current
            f"RETURN r.relationship, v.value"
        )
    
    def query_history(self, entity: str) -> list:
        """Get the full history of an entity."""
        return self.db.query(
            f"MATCH (e {{name: '{entity}'}})-[r]->(v) "
            f"RETURN r.relationship, v.value, r.valid_from, r.valid_to "
            f"ORDER BY r.valid_from"
        )
```

## Autonomous Agent Memory

Autonomous agents (event-triggered, no human initiator) have unique memory requirements. They must reconstruct their context on every invocation.

### The Autonomous Agent Memory Loop

```
Event trigger → Read persistent memory → Decide action → Execute → Update memory → Sleep
```

```python
class AutonomousAgent:
    def __init__(self, memory_store, knowledge_graph):
        self.memory = memory_store
        self.kg = knowledge_graph
    
    def handle_event(self, event: dict):
        """Called on each trigger — must reconstruct context from memory."""
        
        # 1. Read relevant memories
        context = self.memory.similarity_search(
            event["description"], k=10
        )
        
        # 2. Read current knowledge state
        entity_state = self.kg.query_current_state(event["entity"])
        
        # 3. Build context and decide action
        prompt = self._build_prompt(event, context, entity_state)
        decision = model.invoke(prompt)
        
        # 4. Execute action
        result = self._execute(decision)
        
        # 5. Update memory with this interaction
        self.memory.add_texts([
            f"Event: {event['description']}\n"
            f"Decision: {decision}\n"
            f"Result: {result}"
        ])
        
        # 6. Update knowledge graph
        self.kg.record_observation(
            entity=event["entity"],
            attribute="last_action",
            value=str(decision),
            timestamp=datetime.now().isoformat(),
        )
```

### Key Design Considerations for Autonomous Agents

1. **Memory retrieval budget** — Each invocation has limited time. Don't retrieve 100 memories when 5 would suffice. Start with small k and increase only if decision quality suffers.

2. **Memory decay** — Older memories are often less relevant. Weight recent memories higher or use time-decay scoring in your retrieval.

3. **Contradiction handling** — Autonomous agents accumulate memories that may contradict each other (conditions change). The knowledge graph's temporal awareness helps — always check the most recent observation.

4. **Idempotency** — Events may fire multiple times. Memory should help the agent recognise "I've already handled this" to avoid duplicate actions.

## Choosing the Right Long-Term Memory

| Scenario | Recommendation |
|---|---|
| Similar task recall ("I've done this before") | Vector store — semantic similarity |
| Complex domain with entity relationships | Knowledge graph |
| Autonomous agent with evolving state | Knowledge graph + vector store |
| Simple "don't repeat past mistakes" | Vector store with outcome metadata |
| Compliance / audit trail | Knowledge graph with temporal tracking |
| Rapid prototyping | Vector store (simpler to set up) |

Most harnesses start with a vector store. Graduate to a knowledge graph only when you need explicit relationship tracking or temporal awareness.
