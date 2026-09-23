# LangSmith Evaluations

Complete patterns for dataset management, LLM-as-judge evaluation, regression testing, and production monitoring.

## Creating an Eval Dataset

Build a curated dataset of representative inputs and expected outputs.

```python
from langsmith import Client

client = Client()

# Create a named dataset
dataset = client.create_dataset("contract-review-evals")

# Add examples with inputs and expected outputs
client.create_examples(
    inputs=[
        {"contract": "Vendor agrees to 90-day payment terms..."},
        {"contract": "Liability capped at 2x annual fees..."},
    ],
    outputs=[
        {"expected_risk": "medium", "key_clauses": ["payment_terms"]},
        {"expected_risk": "low", "key_clauses": ["liability_cap"]},
    ],
    dataset_id=dataset.id
)
```

**Tips for good datasets:**
- Start with 10-20 examples covering main use cases and edge cases
- Include negative cases (inputs that should be rejected or trigger guardrails)
- Expected outputs can be approximate — they guide LLM-as-judge scoring
- Expand to 50+ examples once the harness stabilises
- Version your datasets — create new ones for major harness changes

## LLM-as-Judge Evaluator

Define custom evaluation criteria in natural language and run them against your dataset.

```python
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator

client = Client()

# Define LLM-as-judge evaluator with custom criteria
correctness_evaluator = LangChainStringEvaluator(
    "labeled_criteria",
    config={
        "criteria": {
            "risk_accuracy": (
                "Does the output correctly identify the risk level? "
                "Compare against the reference risk rating."
            ),
            "clause_coverage": (
                "Does the output identify all key clauses listed "
                "in the reference? Missing clauses should lower the score."
            ),
        }
    }
)

# Define the target function being evaluated
def target_fn(inputs: dict) -> dict:
    """The harness function being evaluated."""
    result = graph.invoke({"contract": inputs["contract"]})
    return {"output": result["analysis"]}

# Run evaluation
results = evaluate(
    target_fn,
    data="contract-review-evals",
    evaluators=[correctness_evaluator],
    experiment_prefix="v1.2-sonnet",  # Tag for comparison
)
```

## Custom Criteria Design

Good evaluation criteria are specific, measurable, and tied to your harness's purpose.

**Example criteria for different harness types:**

Contract review:
- `risk_accuracy`: "Does the output correctly identify the risk level?"
- `clause_coverage`: "Does the output identify all key clauses?"
- `actionability`: "Are recommendations specific enough to act on?"

Code generation:
- `correctness`: "Does the code compile and pass tests?"
- `readability`: "Is the code well-structured with clear naming?"
- `completeness`: "Does the code handle edge cases?"

Content generation:
- `relevance`: "Does the output address the specific question asked?"
- `originality`: "Does the output avoid generic AI-sounding language?"
- `accuracy`: "Are all factual claims verifiable?"

## Regression Testing with Comparison

Run the same dataset against different harness versions and compare side-by-side.

```python
# Run v1 of the harness
results_v1 = evaluate(
    target_fn_v1,
    data="contract-review-evals",
    evaluators=[correctness_evaluator],
    experiment_prefix="v1-opus",
)

# Run v2 with a different model
results_v2 = evaluate(
    target_fn_v2,
    data="contract-review-evals",
    evaluators=[correctness_evaluator],
    experiment_prefix="v2-sonnet",
)

# Compare in LangSmith UI — side-by-side dashboards
# Navigate to: app.smith.langchain.com → Datasets → contract-review-evals → Compare
```

**What to compare:**
- Different models (is the cheaper model good enough?)
- Different prompts (which system prompt performs better?)
- Different graph topologies (does the new architecture improve quality?)
- Different tool sets (does adding a tool help or hurt?)

## Online Evaluation (Production Monitoring)

Attach evaluators to live traces for continuous quality monitoring.

```python
from langsmith import Client
from langsmith.run_helpers import traceable

client = Client()

# Trace every production run
@traceable(run_type="chain", project_name="production-harness")
def production_harness(input_data: dict) -> dict:
    """Traced production run — visible in LangSmith."""
    result = graph.invoke(input_data)
    return result

# Post-hoc evaluation on production traces
# Attach feedback to specific runs
client.create_feedback(
    run_id=run.id,
    key="hallucination_check",
    score=1.0 if grounded else 0.0,
    comment="All claims supported by retrieved context"
)
```

**Production monitoring strategy:**
- Sample a percentage of production traces for automated evaluation (e.g., 10%)
- Use cheap/fast models for online judges to minimise latency and cost
- Set up alerts for quality score drops (e.g., average correctness < 0.8)
- Route low-scoring traces to human annotation queues for review

## Human Annotation Queues

Route samples to subject-matter experts for evaluation.

- Create annotation queues in LangSmith for different evaluation dimensions
- Route edge cases (evaluator disagreements, borderline scores) to experts
- Use human ratings to calibrate your LLM-as-judge evaluators
- Track inter-annotator agreement to ensure consistency

## LangSmith Observability for Harnesses

Beyond evaluation, LangSmith provides:
- **Tracing:** Every LLM call, tool invocation, and state transition traced automatically
- **Token & cost tracking:** Per-node and total token usage against your cost budget
- **Latency monitoring:** Time spent in each node, identify bottlenecks
- **Error debugging:** Drill into failed runs, inspect state at each checkpoint
