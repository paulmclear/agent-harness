# Authoring Agent Skills

How to write effective agent skills — self-contained markdown files that tell an agent *how* to do a specific task.

## Skill Structure

A skill file follows this general structure:

```markdown
# [Skill Name]

## Purpose
One sentence: what this skill enables the agent to do.

## When to Use
Conditions that should trigger this skill.

## Procedure
Step-by-step instructions the agent must follow.

## Output Format
The exact structure/schema the agent must produce.

## Examples
Input/output pairs showing correct behaviour.

## Edge Cases
How to handle unusual inputs or ambiguous situations.
```

## Writing Principles

### 1. Be Procedural, Not Descriptive

Skills should read like a recipe — specific steps in order — not like a textbook.

**Bad (descriptive):**
```
Contract clauses can be complex and may contain multiple obligations. 
It's important to carefully identify each party's responsibilities.
```

**Good (procedural):**
```
For each clause in the contract:
1. Identify the clause type (obligation, right, condition, warranty, limitation)
2. Extract the parties involved
3. List each specific obligation or right
4. Note any deadlines or conditions
5. Flag any penalties for non-compliance
```

### 2. Define Output Schemas Explicitly

Don't let the agent decide the output format. Specify it precisely.

```markdown
## Output Format

Return a JSON array where each element has this structure:
{
  "clause_id": "string — sequential identifier (C001, C002, ...)",
  "clause_type": "obligation | right | condition | warranty | limitation",
  "parties": ["string — party names"],
  "summary": "string — one-sentence summary of the clause",
  "risk_level": "low | medium | high | critical",
  "risk_rationale": "string — why this risk level was assigned"
}
```

### 3. Include Decision Rules

When the procedure involves judgment calls, provide explicit decision criteria.

```markdown
## Risk Assessment Criteria

Assign risk levels based on these rules:
- **Critical:** Uncapped liability, unlimited indemnification, or no termination clause
- **High:** Liability exceeds 5x annual contract value, or auto-renewal without notice
- **Medium:** Non-standard payment terms (> 60 days), or broad non-compete scope
- **Low:** Standard terms with minor deviations from company template
```

### 4. Handle Edge Cases

Anticipate where the agent might go wrong and provide explicit guidance.

```markdown
## Edge Cases

- **Clause references another document:** Note the reference but do not attempt to 
  retrieve or analyse the referenced document. Flag as "external reference — manual review needed."
- **Ambiguous language:** If a clause is genuinely ambiguous, classify it as the 
  higher risk level and note the ambiguity in your rationale.
- **Duplicate clauses:** If the same obligation appears in multiple clauses, 
  analyse each independently but note the duplication.
```

### 5. Keep It Compact

Skills live in system prompts, so they consume context budget. Target < 2K tokens (roughly 1-2 pages of markdown). If a skill is growing beyond this:

- Split it into multiple smaller skills (one per sub-task)
- Move reference tables and examples into a separate file that gets loaded only when needed
- Consider whether the large knowledge component should be a playbook (RAG) instead

## Skill Templates

### Extraction Skill Template

```markdown
# [Domain] Extraction Skill

## Procedure
1. Read the input document carefully
2. Identify all instances of [target entity type]
3. For each instance, extract the following fields: [field list]
4. Validate extracted data against [validation rules]
5. Return structured output

## Output Format
[JSON schema]

## Validation Rules
- [Rule 1]
- [Rule 2]

## Examples
**Input:** [Sample input]
**Output:** [Expected structured output]
```

### Analysis Skill Template

```markdown
# [Domain] Analysis Skill

## Procedure
1. Review the extracted data from the previous phase
2. For each item, evaluate against [criteria]
3. Assign a score/classification using the decision rules below
4. Provide a rationale grounded in [reference material / company policy]
5. Generate actionable recommendations

## Decision Rules
[Explicit criteria for each classification level]

## Output Format
[JSON schema with scores, rationales, and recommendations]
```

### Generation Skill Template

```markdown
# [Domain] Generation Skill

## Procedure
1. Collect all analysis results from previous phases
2. Organise findings by [grouping logic]
3. Generate output using the template below
4. Ensure all [required sections] are present
5. Verify [quality checks] before returning

## Output Template
[Document structure with placeholders]

## Quality Checks
- [ ] All required sections present
- [ ] No placeholder text remaining
- [ ] Recommendations are specific and actionable
- [ ] All claims are grounded in analysis data
```

## Skill Injection Patterns

### Direct System Prompt Injection

The simplest pattern — load the skill markdown directly into the system prompt.

```python
def build_agent_prompt(skill_path: str) -> str:
    with open(skill_path) as f:
        skill = f.read()
    return f"You are a specialist agent.\n\n{skill}"
```

### Tool Definition Injection

For skills that define how to use a specific tool, embed the skill in the tool's docstring.

```python
@tool
def extract_clauses(document: str) -> dict:
    """Extract contract clauses from the document.
    
    Follow this procedure exactly:
    1. Identify each distinct clause
    2. Classify by type: obligation, right, condition, warranty, limitation
    3. Extract parties, obligations, deadlines, penalties
    4. Return as JSON array with schema: [...]
    """
    # Tool implementation
```

### Phase-Based Injection

In multi-phase harnesses, inject different skills at different phases.

```python
PHASE_SKILLS = {
    "extract": "skills/extraction.md",
    "classify": "skills/classification.md",
    "analyse": "skills/risk-analysis.md",
    "generate": "skills/report-generation.md",
}

def get_skill_for_phase(phase: str) -> str:
    path = PHASE_SKILLS.get(phase)
    if path:
        with open(path) as f:
            return f.read()
    return ""
```

## Testing Skills

Skills are probabilistic — the agent may not follow them perfectly every time. Test by:

1. **Format compliance** — Does the output match the specified schema?
2. **Step coverage** — Did the agent perform all required steps?
3. **Decision rule adherence** — Did the agent apply the decision criteria correctly?
4. **Edge case handling** — Does the agent handle unusual inputs as specified?

Run these checks with LangSmith evaluators or DeepEval test cases to track skill adherence over time.
