# Architecture Decision Framework

Use this flowchart logic to select the right harness architecture. Work through each step sequentially — earlier steps constrain later choices.

## Step 1: Scope

Ask: "What kind of task is this?"

- **Well-defined with predictable steps?** → Specialized harness
  - Fixed multi-stage workflows where each phase is known upfront
  - Examples: contract review (8 phases), compliance audit, document processing pipeline
  - You know the exact sequence: Extract → Classify → Analyse → Generate → Review

- **Open-ended / exploratory?** → General-purpose harness
  - Broad capability, flexible tool use, task varies each run
  - Examples: Claude Code, coding assistants, research agents
  - The agent figures out what to do based on the request

- **Event-triggered with no human initiator?** → Autonomous harness
  - Runs on triggers (webhooks, schedules, monitoring alerts)
  - Self-directed with persistent memory across invocations
  - Examples: monitoring bots, automated responders, continuous learning systems

## Step 2: Scale

Ask: "Does it need to process many items simultaneously?"

- **Needs parallel processing across many items?** → Hierarchical / Multi-agent or DAG-based
  - Processing 34 contract clauses simultaneously
  - Analysing multiple documents in a batch
  - Any fan-out / fan-in pattern

- **Single-threaded is fine?** → Keep it simple
  - One item at a time, sequential processing
  - Don't add multi-agent complexity unless you need it

## Step 3: Complexity

Ask: "Can one agent handle it in one context window?"

- **Fits comfortably in one context window?** → Single agent, minimal harness
  - Task is bounded, outputs are small
  - Don't over-engineer — start here and add complexity only when the model demonstrably needs it

- **Exceeds one context window?** → Add context resets, sub-agents, or sprints
  - Long-running tasks (hours of work)
  - Lots of intermediate output that would flood context
  - Use the Initialiser/Coder pattern: break into features, work one at a time, commit, handoff

- **Requires multiple specialised capabilities?** → Multi-agent with dedicated toolsets
  - Different phases need different tools, models, or expertise
  - Example: one agent for code generation, another for testing, another for documentation

## Step 4: Reliability Requirement

Ask: "What's the cost of failure?"

- **90% is fine (internal/experimental):**
  - Minimal harness, dynamic planning
  - Let the model figure things out
  - Quick iteration, accept some failures

- **99% needed (production-facing):**
  - Fixed plans, validation loops, programmatic output generation
  - Generate → test → fix cycles
  - Structured state management

- **99.9% needed (business-critical):**
  - Full harness: fixed plans, adversarial evaluation, human gates, test suites
  - Every output validated before delivery
  - Comprehensive guardrails at all three layers
  - Continuous monitoring via LangSmith

## Step 5: Evaluation Type

Ask: "How do you know if the output is good?"

- **Output is objectively verifiable** (code, data, structured output):
  - Programmatic test loops — generate code → run tests → fix failures → repeat
  - Linters, type checkers, test suites — verifiable sources that can't lie
  - The Ralph Wiggum Loop: run in a loop, check against verifiable sources, explicit stop conditions

- **Output is subjective** (design, writing, legal analysis):
  - Adversarial evaluator with graded criteria
  - GAN-inspired: generator creates, evaluator judges, loop until criteria met
  - Three requirements for effective evaluators:
    1. Make subjective quality gradable (define specific principles, not "is this beautiful?")
    2. Weight criteria toward model weaknesses (score harder on what it struggles with)
    3. Let the evaluator interact with the output (Playwright MCP for web UIs, file inspection)

- **Mixed (code + subjective):**
  - Layer both: programmatic tests for correctness, adversarial evaluator for quality
  - Example: code must pass tests AND meet design quality criteria

## Decision Matrix (Quick Reference)

| Scenario | Architecture | Planning | Evaluation |
|---|---|---|---|
| 8-phase contract review | Specialized | Fixed | Adversarial evaluator + fact-checking |
| General coding assistant | General-purpose | Dynamic | Programmatic (test suites) |
| Monitoring/alerting bot | Autonomous | Dynamic | Programmatic (response validation) |
| Batch document processing | Hierarchical + DAG | Fixed | Programmatic + human spot-check |
| Creative content pipeline | Specialized | Hybrid | Adversarial evaluator (graded criteria) |
| Full-stack app builder | General-purpose | Hybrid (sprints) | Programmatic + adversarial |

## Anti-Patterns to Avoid

1. **Over-engineering** — Don't build a full hierarchical multi-agent system when a single agent with a fixed plan would work. Start simple, add complexity only when the model demonstrably fails.

2. **Dynamic planning for fixed workflows** — If you know the steps upfront, hard-code them. Dynamic planning adds unreliability for no benefit in deterministic workflows.

3. **Self-evaluation** — Never ask an agent to evaluate its own work. It will praise itself even when quality is mediocre. Always use a separate evaluator agent or programmatic tests.

4. **Ignoring context anxiety** — As context fills, models rush and declare things done prematurely. Plan for context management from the start, don't bolt it on later.

5. **One model for everything** — Use expensive models (Opus) for orchestration and evaluation, cheap models (Flash, Haiku) for narrow sub-tasks. Match model tier to task complexity.
