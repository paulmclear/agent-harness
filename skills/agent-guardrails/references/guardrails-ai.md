# Guardrails AI — Output Validation

Validator hub with pre-built and custom validators for checking LLM outputs. Strong at structured output validation, content filtering, and PII scrubbing.

## Core Concept

Guardrails AI provides a `Guard` object that wraps LLM calls and validates outputs against a chain of validators. When validation fails, it can auto-fix, re-prompt, or refuse — configurable per validator.

## Basic Usage — Composing Validators

```python
from guardrails import Guard
from guardrails.hub import (
    CompetitorCheck,
    ToxicLanguage,
    DetectPII,
    ValidJSON,
)

# Compose a guard with multiple validators
guard = Guard().use_many(
    CompetitorCheck(
        competitors=["CompanyX", "CompanyY", "CompanyZ"],
        on_fail="fix",  # Auto-fix by removing competitor mentions
    ),
    ToxicLanguage(
        threshold=0.8,
        on_fail="refrain",  # Refuse to return the output
    ),
    DetectPII(
        pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "SSN"],
        on_fail="fix",  # Auto-redact PII from output
    ),
    ValidJSON(
        on_fail="reask",  # Re-prompt the LLM if output isn't valid JSON
    ),
)

# Use the guard to validate LLM output
result = guard(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Analyse this contract..."}],
)

print(result.validated_output)  # Clean, validated output
print(result.validation_passed)  # True/False
print(result.error)              # Error details if failed
```

## Available Validators (Hub)

Common validators from the Guardrails AI hub:

| Validator | What it checks | on_fail options |
|---|---|---|
| `CompetitorCheck` | Mentions of specified competitors | fix, refrain, noop |
| `ToxicLanguage` | Toxic, offensive, or harmful language | fix, refrain, noop |
| `DetectPII` | Personal identifiable information (email, phone, SSN, etc.) | fix, refrain, noop |
| `ValidJSON` | Output is valid JSON | reask, fix, refrain |
| `ReadingTime` | Output length within acceptable bounds | fix, refrain |
| `ProfanityFree` | No profanity in output | fix, refrain |
| `RestrictToTopic` | Output stays on specified topic | refrain |
| `ValidSQL` | Output is valid SQL | reask, fix |
| `ValidPython` | Output is valid Python | reask, fix |

### on_fail Options

| Option | Behaviour |
|---|---|
| `fix` | Auto-fix the output (remove PII, strip competitor mentions, etc.) |
| `reask` | Re-prompt the LLM with feedback about what failed |
| `refrain` | Return None — refuse to provide the output |
| `noop` | Log the failure but return the output unchanged |
| `exception` | Raise an exception |

## LCEL Integration (LangChain Pipelines)

Convert a Guard to a LangChain-compatible Runnable for use in LCEL pipelines.

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# Create the guard
guard = Guard().use_many(
    CompetitorCheck(competitors=["CompanyX"], on_fail="fix"),
    ToxicLanguage(threshold=0.8, on_fail="refrain"),
)

# Convert to LangChain Runnable
guard_runnable = guard.to_runnable()

# Use in an LCEL pipeline
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
])
model = ChatAnthropic(model="claude-sonnet-4-20250514")

# Guard runs as the final step — validates model output
chain = prompt | model | guard_runnable
result = chain.invoke({"input": "Analyse this contract..."})
```

## Custom Validators

Create domain-specific validators when the hub doesn't have what you need.

```python
from guardrails.validators import (
    FailResult,
    PassResult,
    Validator,
    register_validator,
)

@register_validator(name="custom/financial_compliance", data_type="string")
class FinancialComplianceCheck(Validator):
    """Check that financial outputs include required disclaimers."""

    def __init__(self, required_disclaimers: list[str], **kwargs):
        super().__init__(required_disclaimers=required_disclaimers, **kwargs)
        self.required_disclaimers = required_disclaimers

    def validate(self, value: str, metadata: dict) -> PassResult | FailResult:
        missing = [d for d in self.required_disclaimers if d.lower() not in value.lower()]
        if missing:
            return FailResult(
                error_message=f"Missing required disclaimers: {missing}",
                fix_value=value + "\n\n" + "\n".join(missing),
            )
        return PassResult()

# Use the custom validator
guard = Guard().use(
    FinancialComplianceCheck(
        required_disclaimers=[
            "This is not financial advice.",
            "Past performance does not guarantee future results.",
        ],
        on_fail="fix",  # Auto-append missing disclaimers
    )
)
```

## Structured Output Validation

Enforce that LLM outputs conform to a Pydantic schema.

```python
from pydantic import BaseModel, Field
from guardrails import Guard

class ContractAnalysis(BaseModel):
    risk_level: str = Field(
        description="One of: low, medium, high, critical"
    )
    key_clauses: list[str] = Field(
        description="List of identified clauses"
    )
    recommendations: list[str] = Field(
        description="Actionable recommendations"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the analysis (0-1)"
    )

# Create a guard from the Pydantic model
guard = Guard.from_pydantic(
    output_class=ContractAnalysis,
    num_reasks=2,  # Retry up to 2 times if schema validation fails
)

result = guard(
    model="claude-sonnet-4-20250514",
    messages=[{
        "role": "user",
        "content": "Analyse this contract for risk..."
    }],
)

# result.validated_output is a validated ContractAnalysis instance
analysis = result.validated_output
print(f"Risk: {analysis.risk_level}, Clauses: {analysis.key_clauses}")
```

## Combining with Other Guardrail Libraries

Guardrails AI fits naturally as the output validation layer in the recommended stack:

```python
# Full pipeline:
# 1. LangChain @before_agent → deterministic input filtering
# 2. NeMo RunnableRails → dialogue control
# 3. Agent execution
# 4. Guardrails AI → output validation
# 5. LangChain @after_agent → final safety judge

from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=model,
    tools=tools,
    before_agent=before_agent,   # LangChain pre-processing
    after_agent=after_agent,     # LangChain post-processing
)

# Wrap with NeMo (dialogue control)
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
safe_agent = RunnableRails(nemo_config) | agent

# Add Guardrails AI output validation at the chain level
guard_runnable = guard.to_runnable()
validated_pipeline = safe_agent | guard_runnable
```

## Best Practices

1. **Use `fix` for soft issues** (PII redaction, competitor removal) and `refrain` for hard issues (toxicity, harmful content). `reask` is best for format validation.

2. **Chain validators from cheapest to most expensive.** Regex-based validators (PII, profanity) should run before model-based validators (toxicity, competitor check).

3. **Set appropriate thresholds.** Toxicity at 0.8 is strict; 0.5 catches more but has more false positives. Start strict and loosen if needed.

4. **Test validators independently** with known-good and known-bad outputs before wiring into your pipeline.

5. **Log validation results** to LangSmith for monitoring. Track which validators fire most and review false positives.
