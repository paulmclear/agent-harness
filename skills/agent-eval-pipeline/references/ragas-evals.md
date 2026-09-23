# RAGAS Evaluations — RAG-Specific Metrics

Reference-free evaluation metrics for RAG pipelines. RAGAS separates retrieval quality from generation quality, letting you diagnose failures independently.

## Core Metrics

| Metric | What it measures | Diagnoses |
|---|---|---|
| **Faithfulness** | Is the answer grounded in the retrieved context? | Hallucination — model fabricating info not in docs |
| **Answer Relevancy** | Does the answer address the question asked? | Off-topic responses, tangential answers |
| **Context Precision** | Are the retrieved documents relevant to the question? | Retriever returning wrong docs |
| **Context Recall** | Were all relevant documents retrieved? | Retriever missing important docs |

**Key insight:** If faithfulness is high but answer relevancy is low, the generation is the problem. If context precision is low, the retriever is the problem. This separation is what makes RAGAS powerful.

## Running RAGAS Evaluation

```python
from ragas import evaluate as ragas_evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

# Prepare evaluation dataset
eval_data = Dataset.from_dict({
    "question": [
        "What is our policy on data retention?",
        "What are the termination notice requirements?",
    ],
    "answer": [
        "Data must be retained for 7 years per SOX compliance.",
        "Either party may terminate with 90 days written notice.",
    ],
    "contexts": [
        ["SOX compliance requires 7-year data retention..."],
        ["Termination clause: 90 days written notice required..."],
    ],
    "ground_truth": [
        "Data retention period is 7 years under SOX.",
        "90 days written notice for termination.",
    ],
})

# Run evaluation
ragas_results = ragas_evaluate(
    dataset=eval_data,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ],
)

print(ragas_results)
# {"faithfulness": 0.95, "answer_relevancy": 0.88,
#  "context_precision": 0.92, "context_recall": 0.85}
```

## RAGAS + LangSmith Integration

Pipe RAGAS metrics into LangSmith for unified tracking and comparison.

```python
from ragas.integrations.langsmith import evaluate as ragas_langsmith_evaluate

# Run RAGAS evals and log results to LangSmith automatically
results = ragas_langsmith_evaluate(
    dataset_name="rag-pipeline-evals",  # LangSmith dataset
    llm_or_chain_factory=rag_chain,
    metrics=[faithfulness, context_precision],
    experiment_prefix="rag-v2",
)
```

This gives you RAGAS metrics alongside your LangSmith LLM-as-judge scores in the same comparison dashboard.

## Interpreting Results

| Score range | Interpretation | Action |
|---|---|---|
| 0.9+ | Excellent | Maintain; monitor for regression |
| 0.7–0.9 | Good, room for improvement | Investigate low-scoring examples |
| 0.5–0.7 | Needs work | Significant changes needed |
| < 0.5 | Broken | Fundamental issues with retrieval or generation |

### Diagnosis Guide

**Low faithfulness (hallucination):**
- Model is generating info not present in retrieved context
- Fix: Strengthen system prompt grounding instructions, add post-processing hallucination check
- Consider: Is the context insufficient? Maybe context recall is also low.

**Low context precision (wrong docs retrieved):**
- Retriever is pulling irrelevant documents
- Fix: Improve embedding model, tune chunking strategy, add metadata filtering, try hybrid search

**Low context recall (missing docs):**
- Retriever is missing relevant documents
- Fix: Increase k (retrieve more docs), improve chunking overlap, check if important docs are in the corpus

**Low answer relevancy (off-topic):**
- Model is answering a different question than what was asked
- Fix: Improve system prompt question-focus instructions, add answer relevancy check

## Chunking Strategy Impact

RAGAS results are heavily influenced by your chunking strategy. Experiment with:

| Parameter | Range to try | Impact |
|---|---|---|
| Chunk size | 256–2048 tokens | Smaller = more precise retrieval, larger = more context per chunk |
| Chunk overlap | 50–200 tokens | More overlap = less chance of splitting relevant content |
| Splitter type | RecursiveCharacterTextSplitter (recommended) | Respects document structure (headings, paragraphs) |

Run RAGAS after each chunking change to measure the impact quantitatively.
