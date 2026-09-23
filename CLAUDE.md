# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Package manager is **uv** (see `uv.lock`, `.python-version` pins 3.11+).

- Install deps: `uv sync`
- Run the one-shot research agent: `uv run python agent.py`
- Run the interactive REPL agent: `uv run python cli_agent.py` (commands: `chat <msg>`, `research <topic>`, `exit`)
- Entry stub: `uv run python main.py`

Requires `.env` with `OPENAI_API_KEY` and `TAVILY_API_KEY`. There is no test suite, linter config, or build step in this repo yet.

## Architecture

This is an **experimental sandbox for building agent harnesses** — the surrounding software that puts LLMs on deterministic rails. The repo has two layers:

### 1. Runnable prototypes (root `.py` files)

Both `agent.py` and `cli_agent.py` construct a **deepagents** agent (`create_deep_agent`) wired identically:

- Model: `openai:gpt-5-mini`
- Backend: `FilesystemBackend(root_dir='./sandbox/', virtual_mode=True)` — the agent's filesystem writes are sandboxed here. `virtual_mode=True` means writes are in-memory unless flushed; `sandbox/` is the durable scratch dir.
- Tool: `internet_search` from `search_tool.py`, a thin Tavily wrapper.
- `agent.py` is a single-shot research task; `cli_agent.py` wraps the same agent in a `cmd.Cmd` REPL with a `MemorySaver` checkpointer keyed by a per-session `thread_id` for multi-turn memory.

When modifying agent construction, keep both files in sync unless intentionally diverging — they share the same tool and backend conventions.

### 2. Skills library (`skills/<name>/`)

Six skills (each a folder containing `SKILL.md` + `references/`) that form an opinionated end-to-end playbook for production agent harnesses on the **LangGraph + LangSmith + RAGAS + DeepEval + NeMo/Guardrails AI** stack. They split by lifecycle phase and cross-reference each other:

| Skill | Phase | Purpose |
|---|---|---|
| `agent-harness-architect` | Design | Architecture selection, harness design docs |
| `langgraph-harness-builder` | Implementation | LangGraph code patterns (StateGraph, ToolNode, checkpointing, fan-out, subgraphs) |
| `agent-skills-and-playbooks` | Knowledge | Two-tier grounding: procedural Skills vs RAG Playbooks |
| `agent-memory-design` | Memory | Working / file-based / long-term memory + context compaction |
| `agent-guardrails` | Runtime control | Input/output validation, HITL, PII, injection defense |
| `agent-eval-pipeline` | Build-time eval | LangSmith + RAGAS + DeepEval, LLM-as-judge, CI regression |

The skills are the authoritative reference for *how* this repo thinks harnesses should be built. When the user asks design or implementation questions about agents, RAG, guardrails, evals, or memory, invoke the matching skill via the Skill tool rather than answering from general knowledge — the stack choices are opinionated and the skills contain the preferred patterns.

Note: the runnable prototypes currently use `deepagents`, not raw LangGraph. The skills describe the target stack; the root scripts are the current starting point.

## Other directories

- `sandbox/` — agent filesystem output (gitignored scratch).
- `transcripts/` — saved agent run transcripts.
- `docs/` — local notes.
