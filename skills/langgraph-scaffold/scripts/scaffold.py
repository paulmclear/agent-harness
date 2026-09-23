#!/usr/bin/env python3
"""Scaffold a LangGraph workflow package from ../templates.

Run from the project root (the directory that makes the package importable):

    uv run python ~/.claude/skills/langgraph-scaffold/scripts/scaffold.py workflows/practice/l3

Placeholders replaced in every ``*.tmpl`` file:
    __PACKAGE__     dotted import path, derived from the target dir
    __NAME__        last path segment
    __ENV_PREFIX__  settings env prefix, e.g. ``L3_``
"""

import argparse
import keyword
import logging
import re
import shutil
import sys
import tomllib
from pathlib import Path

logger = logging.getLogger("scaffold")

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE_SUFFIX = ".tmpl"
REQUIRED_DEPS = [
    "langchain",
    "langgraph",
    "pydantic-settings",
    "python-dotenv",
    "pyyaml",
    "typesafe-sdk",
]
DEV_DEPS = ["pytest", "ruff"]


def derive_package(target: Path, root: Path) -> str:
    try:
        parts = target.resolve().relative_to(root.resolve()).parts
    except ValueError:
        sys.exit(f"error: {target} is not inside the project root {root}")
    bad = [p for p in parts if not p.isidentifier() or keyword.iskeyword(p)]
    if not parts or bad:
        sys.exit(f"error: path segments must be valid Python identifiers: {bad or parts}")
    return ".".join(parts)


def render(text: str, substitutions: dict[str, str]) -> str:
    for placeholder, value in substitutions.items():
        text = text.replace(placeholder, value)
    return text


def declared_deps(pyproject: Path) -> set[str]:
    data = tomllib.loads(pyproject.read_text())
    specs = list(data.get("project", {}).get("dependencies", []))
    for group in data.get("dependency-groups", {}).values():
        specs += [s for s in group if isinstance(s, str)]
    return {re.split(r"[<>=!~\[; ]", s, maxsplit=1)[0].lower() for s in specs}


def scaffold(target: Path, substitutions: dict[str, str], force: bool) -> list[Path]:
    if target.exists() and any(target.iterdir()) and not force:
        sys.exit(f"error: {target} is not empty (use --force to overwrite)")

    written = []
    for src in sorted(TEMPLATES.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(TEMPLATES)
        dest = target / (rel.with_suffix("") if src.suffix == TEMPLATE_SUFFIX else rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix == TEMPLATE_SUFFIX:
            dest.write_text(render(src.read_text(), substitutions))
        else:
            shutil.copyfile(src, dest)
        written.append(dest)
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", type=Path, help="Directory to create, e.g. workflows/l3")
    parser.add_argument("--package", help="Dotted import path (default: derived from target)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root")
    parser.add_argument("--force", action="store_true", help="Overwrite a non-empty target")
    args = parser.parse_args()

    package = args.package or derive_package(args.target, args.root)
    name = package.rsplit(".", 1)[-1]
    substitutions = {
        "__PACKAGE__": package,
        "__NAME__": name,
        "__ENV_PREFIX__": f"{name.upper()}_",
    }

    for path in scaffold(args.target, substitutions, args.force):
        logger.info("created %s", path)

    pyproject = args.root / "pyproject.toml"
    if pyproject.exists():
        have = declared_deps(pyproject)
        missing = [d for d in REQUIRED_DEPS if d not in have]
        missing_dev = [d for d in DEV_DEPS if d not in have]
        if missing:
            logger.info("\nmissing deps: uv add %s", " ".join(missing))
        if missing_dev:
            logger.info("missing dev deps: uv add --dev %s", " ".join(missing_dev))

    logger.info("\npackage: %s", package)
    logger.info("verify:  uv run python -m pytest %s", args.target)
    logger.info("dry run: uv run python -m %s.graph --debug --input topic=test", package)


if __name__ == "__main__":
    main()
