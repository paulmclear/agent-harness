# Project Checklist

Run through this before, during, and after any harness build.

## Pre-Build

- [ ] Problem clearly defined — what fails without a harness?
- [ ] Architecture selected with rationale
- [ ] Planning strategy chosen (fixed / dynamic / hybrid)
- [ ] Agent roster defined with model choices and context budgets
- [ ] Tool calling pattern(s) selected
- [ ] Memory design documented
- [ ] Skills identified and authored (procedural markdown files)
- [ ] Playbook / knowledge base defined (document corpus, chunking, embedding model, vector store)
- [ ] Playbook retrieval phase mapped in harness workflow
- [ ] State management approach chosen
- [ ] Validation strategy defined (LangSmith evaluators + RAGAS metrics + DeepEval tests)
- [ ] Guardrails strategy defined (input/tool-level/output layers, libraries selected)
- [ ] Human-in-the-loop touchpoints identified
- [ ] Cost and performance budget set
- [ ] Assumptions logged
- [ ] Baseline eval dataset created in LangSmith

## During Build

- [ ] Harness engine code handles state transitions
- [ ] Sub-agent prompts are dedicated and lean
- [ ] Context management is active (compaction, file-based summaries)
- [ ] Validation loops are wired in (not ad-hoc)
- [ ] Tool bridge is secure (session auth, no direct internet from sandbox)
- [ ] Progress/state is observable (logging, status tracking)
- [ ] LangSmith tracing enabled and verified for all nodes
- [ ] LangSmith eval dataset created with representative inputs/outputs
- [ ] Guardrails wired in — pre-processing, tool-level, and post-processing
- [ ] Guardrail triggers observable in LangSmith traces
- [ ] Playbook knowledge base indexed and retrieval verified
- [ ] Skills loaded into correct agent prompts
- [ ] RAGAS metrics configured for any RAG / playbook retrieval components
- [ ] DeepEval test suite created for CI/CD gating

## Post-Build

- [ ] End-to-end test with representative input
- [ ] Token usage measured against budget (verify in LangSmith traces)
- [ ] Cost measured against ceiling (LangSmith cost dashboard)
- [ ] LangSmith regression evals passing
- [ ] DeepEval CI tests passing with quality thresholds
- [ ] Guardrail false positive rate reviewed
- [ ] Online evaluators attached to production traces
- [ ] Assumptions reviewed — any already stale?
- [ ] Harness documented for handoff / iteration
