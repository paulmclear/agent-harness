import datetime as dt
import logging
from collections.abc import Callable, Mapping, Sequence
from functools import cache
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from workflows.practice.l2.config import get_settings
from workflows.practice.l2.state import State

logger = logging.getLogger(__name__)


def format_user_prompt(template: str, values: Mapping[str, Any]) -> str:
    """Fill ``template`` with ``{current_date}`` plus every key in ``values``."""
    return template.format(current_date=dt.date.today().isoformat(), **values)


def make_agent_node(
    *,
    name: str,
    system_prompt: str,
    user_prompt_template: str,
    output_state_key: str,
    tools: Sequence[Any] = (),
    model: str | None = None,
    response_format: type[BaseModel] | None = None,
    prompt_inputs: Callable[[State], Mapping[str, Any]] | None = None,
    middleware: Callable[[], Sequence[Any]] | None = None,
    parse_response: Callable[[dict], Any] | None = None,
) -> Callable[[State], dict]:
    """Build a LangGraph node that runs a single-turn agent.

    The node formats ``user_prompt_template`` (see ``format_user_prompt``),
    invokes the agent, and writes the result to ``state[output_state_key]``.
    When ``state["debug"]`` is set it logs the prompt and skips the model,
    writing ``""`` (or ``None`` for structured output).

    Args:
        response_format: Pydantic model for structured output. When set, the
            node writes the parsed model instead of the final message text.
        prompt_inputs: Builds the template values from the state. Defaults to
            the state itself; use it when the prompt needs derived or
            pre-formatted values rather than raw state keys.
        middleware: Returns the agent middleware (e.g. tool-call limits).
            Called when the agent is first built, so it can read settings.
        parse_response: Maps the raw agent response to the value written to
            state, overriding the default (structured response or final text).
            In debug mode the node skips the model and this hook.

    The agent is built on first real call, so importing the graph or running
    in debug mode never needs API keys.
    """

    @cache
    def get_agent():
        return create_agent(
            name=name,
            system_prompt=system_prompt,
            model=model or get_settings().default_model,
            tools=list(tools) or None,
            response_format=response_format,
            middleware=list(middleware()) if middleware else (),
        )

    def node(state: State) -> dict:
        values = prompt_inputs(state) if prompt_inputs else state
        user_prompt = format_user_prompt(user_prompt_template, values)

        if state.get("debug"):
            logger.info("[%s] user prompt:\n%s", name, user_prompt)
            return {output_state_key: None if response_format else ""}

        response = get_agent().invoke({"messages": [HumanMessage(content=user_prompt)]})
        if parse_response:
            return {output_state_key: parse_response(response)}
        if response_format:
            return {output_state_key: response["structured_response"]}
        return {output_state_key: response["messages"][-1].content}

    return node
