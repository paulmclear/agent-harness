# Validation & Evaluation Strategy

Two distinct layers every harness needs: **build-time evals** (does it work?) and **runtime validation** (keep it reliable per-run).

## Build-Time Evaluation

Evaluations run during development and CI to catch regressions before deployment.

### Evaluation Dimensions

| What you're evaluating | Metrics | Tool | Notes |
|---|---|---|---|
| Output quality (general) | Correctness, relevance, coherence, tone | LangSmith evaluators | LLM-as-judge with custom criteria. Supports pairwise comparison. |
| Output quality (RAG) | Faithfulness, answer relevance, context precision/recall | RAGAS | Reference-free. Separates retrieval from generation quality. |
| Retrieval quality | Context precision, context recall, noise sensitivity | RAGAS + LangSmith | Diagnose retrieval vs generation failures independently. |
| Hallucination detection | Groundedness | RAGAS faithfulness + LangSmith | Flag responses with info not in retrieved context. |
| Unit-test style LLM testing | Pass/fail assertions | DeepEval | Pytest-native. CI/CD gating with quality thresholds. |
| Regression testing | Score comparison across changes | LangSmith comparison | Side-by-side experiment dashboards. |
| Human evaluation | Expert judgment, annotation | LangSmith annotation queues | Route to SMEs. Calibrate automated evaluators. |

### Recommended Eval Stack

**LangSmith** (platform) + **RAGAS** (RAG metrics) + **DeepEval** (CI/CD test runner)

- **LangSmith** is the hub — dataset management, experiment tracking, comparison, human annotation, online + offline eval
- **RAGAS** plugs into LangSmith for specialised RAG metrics without needing manually labelled ground truth
- **DeepEval** adds pytest-style assertions for CI/CD — fail a deploy if quality drops below threshold

### Eval Workflow

1. **Create baseline dataset** in LangSmith with representative inputs and expected outputs
2. **Define evaluators** — LangSmith LLM-as-judge for general quality + RAGAS for retrieval/generation split
3. **Run offline evals** during development — compare experiments across prompt, model, or topology changes
4. **Wire into CI** — DeepEval test suites gate deployments on quality thresholds
5. **Add human annotation** — route edge cases to domain experts via LangSmith annotation queues
6. **Run online evals** in production — attach LLM-as-judge evaluators to live LangSmith traces

## Runtime Validation Loops

Quality mechanisms that run during each harness execution.

### Programmatic Test Loops (Objective Output)

For code, data, structured output — anything with a verifiable correct answer.

**Pattern:** Generate → Test → Fix → Repeat

- Agent generates code
- Harness runs tests (pytest, Jest, linters, type checkers)
- If tests fail, feed errors back to agent for revision
- Explicit stop conditions: all tests pass, or max iterations reached

**The Ralph Wiggum Loop:** Run an agent in a loop, checking output against verifiable sources that can't lie. Explicit stop conditions keep the loop running until truly done.

**Key example:** Stripe's harness runs generated code against a subset of their 3M test suite → 1,300 merged PRs per week.

### Adversarial Evaluator Loop (Subjective Output)

For writing, design, legal analysis — anything where quality is a judgment call.

**Pattern:** Generator creates → Evaluator judges → Loop until criteria met (GAN-inspired)

**Three requirements for effective evaluator agents:**

1. **Make subjective quality gradable** — Don't ask "is this beautiful?" Define specific principles with scoring criteria.
   - Example criteria: design quality, originality (anti-AI-slop), craft (technical execution), functionality

2. **Weight criteria toward model weaknesses** — If the model scores well on 2/4 criteria but struggles on others, weight the weak areas heavier to compensate.

3. **Let the evaluator interact with the output** — Use Playwright MCP so the evaluator can navigate the app, screenshot it, and test it like a real user. Don't just ask it to read code.

**Important warning:** Out of the box, LLMs are poor QA agents. They identify legitimate issues, then talk themselves into deciding they aren't a big deal and approve anyway. Multiple rounds of iteration on evaluator prompts are typically needed.

### Fact-Checking Loops

For factual claims — cross-reference against source material.

**Pattern:** Extract claims → Check each against retrieved documents → Flag unsupported claims → Revise

### Human-in-the-Loop Gates

For high-stakes actions where automated validation isn't sufficient.

**When to use:**
- External API calls (publishing, sending emails, modifying production data)
- Actions with legal or financial consequences
- Cases where the cost of error exceeds the cost of human review

**Implementation:** LangGraph `interrupt_before` on specific nodes. Graph pauses, human reviews, graph resumes with `Command(resume=...)`. Requires a checkpointer for persistence.

### Contract Negotiation Pattern

For multi-sprint work, the generator and evaluator agree on a "definition of done" upfront per sprint. This prevents scope creep and ensures the evaluator has clear, pre-negotiated criteria rather than moving goalposts.
