import logging
from collections.abc import Callable
from pathlib import Path

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.state import State

logger = logging.getLogger(__name__)


def make_write_output_node(
    *,
    content_key: str,
    filename_template: str,
    path_key: str = "file_path",
    output_dir: Path | None = None,
) -> Callable[[State], dict]:
    """Build a node that writes ``state[content_key]`` to a file.

    ``filename_template`` is formatted with the state, e.g.
    ``"report_{customer_id}.md"``. Files go to ``output_dir`` (default:
    ``settings.output_dir``) and the path is returned under ``path_key``.
    """

    def node(state: State) -> dict:
        directory = output_dir or get_settings().output_dir
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename_template.format(**state)
        path.write_text(state[content_key])
        logger.info("Wrote %s", path)
        return {path_key: str(path)}

    return node
