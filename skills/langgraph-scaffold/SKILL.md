---
name: langgraph-scaffold
description: Scaffolds a new LangGraph workflow package with Paul's standard boilerplate - graph.py (StateGraph build/compile + argparse CLI with --execute/--debug/--output-image), state.py, pydantic-settings config.py with load_dotenv, and reusable utilities (make_agent_node agent factory, write-output node, TypeSafe QA judge node, cached YAML fixture loader) plus a pytest smoke test. Use when the user wants to start, create, scaffold, or bootstrap a new LangGraph workflow, graph, or agent pipeline directory, or asks for their usual LangGraph boilerplate.
---

# LangGraph Scaffold

## Quick start

From the project root (the directory that makes the package importable):

```bash
uv run python ~/.claude/skills/langgraph-scaffold/scripts/scaffold.py workflows/practice/l3
```

The target path becomes the import path (`workflows.practice.l3`), so every
segment must be a valid Python identifier. Use `--package` to override it,
`--force` to write into a non-empty dir.

## Workflow

- [ ] Confirm the target directory with the user if they didn't name one
- [ ] Run `scaffold.py <target>`
- [ ] If it prints `missing deps`, run the `uv add` lines it prints (ask first: it edits pyproject.toml)
- [ ] `uv run ruff check --fix <target> && uv run ruff format <target>`
- [ ] `uv run python -m pytest <target>`: both tests must pass with no API keys
- [ ] Replace the example with the real workflow (see below), keeping tests green

Use `python -m pytest`, not bare `pytest`: it puts the project root on `sys.path` so the absolute package imports resolve.

## What gets generated

```
<target>/
├── graph.py              build_graph() + CLI; START → example_agent → write_output → END
├── state.py              InputState (debug + inputs) and State (derived + outputs)
├── config.py             Settings (default_model, output_dir, OPENAI_API_KEY); load_dotenv lives here
├── agents/
│   ├── _base.py          make_agent_node(): prompt templating, debug dry run, lazy create_agent
│   └── example_agent.py  SYSTEM_PROMPT / USER_PROMPT_TEMPLATE / *_node pattern
├── nodes/
│   ├── write_output_node.py  make_write_output_node(): state key → file, returns path
│   └── qa_node.py        make_qa_node(): TypeSafe system_one judgments over agent output
├── tools/
│   ├── _data.py          @cache'd load_yaml() for fixtures in tools/data/
│   └── data/
└── tests/test_graph.py   compiles + debug run writes output, no model calls
```

## Adapting the example

1. **state.py**: put real inputs on `InputState`, derived keys on `State`.
2. **agents/**: one file per agent. Copy `example_agent.py`. The user prompt
   template may use `{current_date}` and any state key.
3. **nodes/**: one `<verb>_<noun>_node.py` per deterministic step, each returning
   a partial state dict. Use the factories for writing output and QA.
4. **tools/**: pure functions + pydantic models, re-exported from `tools/__init__.py`.
5. **graph.py**: register nodes and edges. Update the `--input` example in the docstring.
6. **tests/test_graph.py**: update the node set and debug-run inputs.

## Conventions baked in

- `load_dotenv()` runs once, in `config.py`. Don't add it to other modules.
- Settings are read through `get_settings()`. Override them with `<NAME>_`-prefixed env vars.
- `state["debug"]` means a dry run: agents log their prompts, QA is skipped, and no API keys are needed.
- Agents are built lazily, so importing the graph never touches the network.
- Use `logging` with module-level loggers, never `print`.
- Run the CLI as `uv run python -m <package>.graph ...`. `graph.png` is written next to `graph.py`.
