---
name: agent-eval-pipeline
description: Set up build-time evaluation and quality assurance for agent harnesses using LangSmith + RAGAS + DeepEval. Use this skill whenever the user wants to evaluate an agent's output quality, set up LLM-as-judge evaluators, create eval datasets, measure RAG pipeline quality (faithfulness, context precision, recall), build CI/CD test suites for LLM outputs, run regression tests across model or prompt changes, set up online/production monitoring for agents, red-team an agent for vulnerabilities, or implement the adversarial generator-evaluator quality loop. Trigger on mentions of "eval", "evaluation", "LangSmith", "RAGAS", "DeepEval", "LLM-as-judge", "agent testing", "quality assurance", "regression testing", "faithfulness", "context precision", "hallucination detection", "red-teaming", "CI/CD for LLMs", or any request to measure or improve agent output quality. This skill covers BUILD-TIME evaluation — for runtime guardrails and safety controls, use the agent-guardrails skill instead.
---

# Agent Eval Pipeline

Best-practice patterns for evaluating agent harness quality using the recommended stack: **LangSmith** (platform) + **RAGAS** (RAG metrics) + **DeepEval** (CI/CD test runner).

## Why Evaluation Matters

Without proper evaluation, you can't know if your harness actually works — or if a prompt change, model swap, or graph restructure made things better or worse. Evaluation is how you cross the gap from "it seems to work" to "we have data showing it works."

## The Three Tools — When to Use Each

| Tool | What it does | When to use |
|---|---|---|
| **LangSmith** | Platform for eval datasets, LLM-as-judge evaluators, experiment comparison, human annotation, online monitoring | Always — it's the hub for everything |
| **RAGAS** | Reference-free RAG evaluation metrics | When your harness has a RAG / retrieval component |
| **DeepEval** | Pytest-native LLM test assertions for CI/CD | When you need automated quality gates in your deployment pipeline |

These tools complement each other. LangSmith is always the foundation. Add RAGAS if you have RAG. Add DeepEval for CI/CD gating.

## Evaluation Dimensions

| What you're evaluating | Metrics | Tool |
|---|---|---|
| Output quality (general) | Correctness, relevance, coherence, tone | LangSmith LLM-as-judge |
| Output quality (RAG) | Faithfulness, answer relevance | RAGAS |
| Retrieval quality | Context precision, context recall | RAGAS |
| Hallucination detection | Groundedness (is response supported by context?) | RAGAS faithfulness + LangSmith |
| Unit-test style assertions | Pass/fail on LLM outputs | DeepEval |
| Regression testing | Score comparison across changes | LangSmith comparison view |
| Human evaluation | Expert judgment, annotation | LangSmith annotation queues |
| Vulnerability testing | Prompt injection, jailbreak resistance | DeepEval red-teaming |

## Eval Workflow — Step by Step

Follow this workflow to set up evaluation for any harness:

### Step 1: Create a Baseline Dataset

Build a dataset in LangSmith with representative inputs and expected outputs. This is your ground truth.

Read `references/langsmith-evals.md` for the dataset creation code pattern.

**Tips for good eval datasets:**
- Cover the main use cases (happy path) AND edge cases
- Include inputs that should trigger guardrails (negative cases)
- Start with 10-20 examples; expand to 50+ once the harness stabilises
- Include expected outputs even if approximate — they calibrate LLM-as-judge evaluators

### Step 2: Define Evaluators

**For general output quality** → Use LangSmith's LLM-as-judge with custom criteria defined in natural language. Example criteria: correctness, completeness, actionability, tone.

**For RAG pipelines** → Add RAGAS metrics: faithfulness (is the answer grounded in retrieved context?), context precision (are retrieved docs relevant?), context recall (were all relevant docs retrieved?), answer relevancy (does the answer address the question?).

Read `references/langsmith-evals.md` for LLM-as-judge setup and `references/ragas-evals.md` for RAGAS metric configuration.

### Step 3: Run Offline Evals

During development, run your harness against the eval dataset and compare experiments:
- Same dataset, different prompts → Which prompt works better?
- Same dataset, different models → Is the cheaper model good enough?
- Same dataset, different graph topologies → Does the new architecture improve quality?

LangSmith's comparison view gives side-by-side experiment dashboards.

### Step 4: Wire into CI/CD

Use DeepEval to create pytest-style test suites that gate deployments on quality thresholds. If correctness drops below 0.7, the deploy fails.

Read `references/deepeval-evals.md` for the CI/CD test suite pattern.

### Step 5: Add Human Annotation

Route edge cases and evaluator disagreements to domain experts via LangSmith annotation queues. Use human feedback to calibrate automated evaluators.

### Step 6: Enable Online Evaluation

Attach LLM-as-judge evaluators to live LangSmith traces for continuous production monitoring. Catch quality degradation before users report it.

Read `references/langsmith-evals.md` for the online evaluation pattern.

## Choosing the Right Eval Approach

| Scenario | Recommended approach |
|---|---|
| General agent (no RAG) | LangSmith LLM-as-judge + DeepEval CI tests |
| RAG-based agent | LangSmith + RAGAS + DeepEval |
| Code generation | Programmatic tests (pytest/Jest) + LangSmith for tracking |
| Subjective output (writing, design) | Adversarial evaluator loop (see langgraph-harness-builder skill) + LangSmith for grading |
| Pre-deployment safety check | DeepEval red-teaming |
| Production monitoring | LangSmith online evaluation |

## Key Principles

1. **Separate retrieval from generation evaluation** — If your RAG pipeline gives bad answers, is it because it retrieved the wrong documents, or because the LLM generated a bad answer from good documents? RAGAS metrics let you diagnose this independently.

2. **Start with offline, graduate to online** — Build your eval dataset and run offline experiments first. Once the harness is in production, add online evaluators for continuous monitoring.

3. **Human annotation calibrates everything** — LLM-as-judge evaluators need calibration. Use LangSmith annotation queues to get expert ratings, then compare against your automated evaluators.

4. **CI/CD gates prevent regression** — Every prompt change, model swap, or graph restructure should pass your DeepEval test suite before deploying.

5. **Track cost alongside quality** — LangSmith traces show token usage per node. A 2% quality improvement isn't worth a 10x cost increase.

## Reference Files

Read these for complete, copy-paste-ready code patterns:

- `references/langsmith-evals.md` — Dataset creation, LLM-as-judge evaluators, online evaluation, comparison experiments
- `references/ragas-evals.md` — RAG metrics (faithfulness, context precision/recall, answer relevancy), LangSmith integration
- `references/deepeval-evals.md` — CI/CD test suites, G-Eval custom metrics, red-teaming for vulnerability scanning
