# DeepEval — CI/CD Test Suites & Red-Teaming

Pytest-native LLM evaluation for gating deployments and vulnerability scanning.

## CI/CD Test Suite

Create test cases with quality threshold assertions. Run with `deepeval test run`.

```python
# test_harness_quality.py — run with: deepeval test run test_harness_quality.py
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    GEval,
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
)

# Custom G-Eval metric — define criteria in natural language
correctness = GEval(
    name="Correctness",
    criteria=(
        "The output correctly identifies risk level and key clauses. "
        "Penalise missed risks or fabricated clauses heavily."
    ),
    evaluation_params=[
        "input", "actual_output", "expected_output"
    ],
    threshold=0.7,  # Minimum score to pass
)

faithfulness = FaithfulnessMetric(threshold=0.8)
hallucination = HallucinationMetric(threshold=0.5)

# Test cases
@pytest.mark.parametrize("test_case", [
    LLMTestCase(
        input="Analyse this NDA for risk",
        actual_output=harness_output_1,
        expected_output="Medium risk: broad non-compete clause",
        retrieval_context=["NDA template with standard non-compete..."],
    ),
    LLMTestCase(
        input="Review this MSA",
        actual_output=harness_output_2,
        expected_output="Low risk: standard liability cap",
        retrieval_context=["MSA with 2x annual fee liability cap..."],
    ),
])
def test_harness_output_quality(test_case):
    assert_test(test_case, [correctness, faithfulness, hallucination])
```

## Available Metrics

### Built-in Metrics

| Metric | What it checks | Typical threshold |
|---|---|---|
| `FaithfulnessMetric` | Is output grounded in retrieval context? | 0.8 |
| `AnswerRelevancyMetric` | Does output address the input question? | 0.7 |
| `HallucinationMetric` | Does output contain fabricated information? | 0.5 (lower = fewer hallucinations) |
| `ContextualPrecisionMetric` | Are retrieved docs relevant? | 0.7 |
| `ContextualRecallMetric` | Were all relevant docs retrieved? | 0.7 |
| `ToxicityMetric` | Is the output toxic or harmful? | 0.5 |
| `BiasMetric` | Does the output show bias? | 0.5 |

### G-Eval (Custom Criteria)

Define any evaluation criterion in natural language. G-Eval uses an LLM to score the output.

```python
from deepeval.metrics import GEval

actionability = GEval(
    name="Actionability",
    criteria=(
        "Are the recommendations specific enough that a business user "
        "could take action on them without needing further clarification? "
        "Vague suggestions like 'consider reviewing' should score low."
    ),
    evaluation_params=["input", "actual_output"],
    threshold=0.6,
)
```

## Red-Teaming (Vulnerability Scanning)

Automated adversarial testing to find security vulnerabilities in your harness.

```python
from deepeval.red_teaming import RedTeamer

red_teamer = RedTeamer(
    target_model=your_model,
    attacks_per_vulnerability=5,
)

# Run red-team attacks
results = red_teamer.scan(
    purpose="Contract review assistant",
    system_prompt="You are a legal analyst...",
    attacks=[
        "prompt_injection",
        "jailbreak",
        "role_playing",
        "context_manipulation",
    ],
)

print(f"Vulnerabilities found: {results.vulnerability_count}")
```

**Available attack types:** DeepEval provides 40+ red-teaming attacks including prompt injection, jailbreak attempts, role-playing exploits, and context manipulation. Run these before deploying any user-facing harness.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Harness Quality Gate
on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install deepeval langchain langgraph
      - name: Run quality tests
        run: deepeval test run tests/test_harness_quality.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Quality Gate Strategy

| Environment | What to test | Threshold |
|---|---|---|
| PR / Feature branch | Core correctness, faithfulness | Strict (0.7+) |
| Staging | Full test suite including edge cases | Moderate (0.6+) |
| Pre-production | Red-teaming + full regression | All must pass |

## Best Practices

1. **Start with 5-10 test cases** covering happy path and key edge cases. Expand as you find failure modes.

2. **Set thresholds conservatively at first** (0.6-0.7), then tighten as the harness improves. Too strict too early blocks iteration.

3. **Run red-teaming before any user-facing deployment.** Prompt injection and jailbreak resistance are table stakes.

4. **Combine DeepEval with LangSmith** — DeepEval gates deploys (pass/fail), LangSmith provides the detailed experiment tracking and comparison dashboards for debugging failures.

5. **Version your test cases** alongside your harness code. When the harness changes, review whether tests need updating.
