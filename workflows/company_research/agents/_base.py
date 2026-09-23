"""Shared factories for the HubSpot Company Research workflow.

Two agent types in this workflow:
  • Research-batch agents — single-shot Perplexity sonar-pro calls that
    take `company_name` from state and produce a JSON blob. Mirrors the
    n8n `n8n-nodes-base.perplexity` node with simplify=true.
  • Analyst agents — single-shot OpenAI gpt-5-mini calls that consume
    the unified researchData + citations and produce a section JSON.
    Mirrors `@n8n/n8n-nodes-langchain.openAi`.
"""

from __future__ import annotations

import json
import os
from typing import Callable, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_perplexity import ChatPerplexity
from pydantic import BaseModel, SecretStr

from workflows.company_research.state import AgentState

load_dotenv()

DEFAULT_ANALYST_MODEL = "gpt-5-mini"
DEFAULT_PERPLEXITY_MODEL = "sonar-pro"

# Identical system prompt used by all six research_batch_X agents in the spec.
RESEARCH_SYSTEM_PROMPT = (
    "You are a financial crime compliance research analyst. Extract precise "
    "structured data. Return valid JSON only. ALWAYS include source URLs in a "
    "'sources' array with objects containing: {url, title, publishedDate}."
)


def _perplexity_chat(system_prompt: str, user_prompt: str, model: str) -> str:
    llm = ChatPerplexity(model=model, timeout=None)
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return response.content if isinstance(response.content, str) else str(response.content)


def _openai_chat(
    user_prompt: str,
    model: str,
    system_prompt: Optional[str] = None,
    output_model: Optional[type[BaseModel]] = None,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model=model,
        api_key=SecretStr(api_key) if api_key else None,
    )

    messages: list = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    elif output_model:
        # json_mode requires at least one message to mention "JSON"
        messages.append(SystemMessage(content="Respond with valid JSON matching the requested schema."))
    messages.append(HumanMessage(content=user_prompt))

    if output_model:
        structured_llm = llm.with_structured_output(
            output_model, method="json_mode", include_raw=True
        )
        raw_result = structured_llm.invoke(messages)
        parsed = raw_result.get("parsed")
        if isinstance(parsed, BaseModel):
            return parsed.model_dump_json()
        # Field-name mismatch or parse error — return the raw text so the
        # final report builder can still consume it as unstructured content.
        raw_msg = raw_result.get("raw")
        if raw_msg is not None:
            content = raw_msg.content
            return content if isinstance(content, str) else json.dumps(content)
        return "{}"

    response = llm.invoke(messages)
    content = response.content
    return content if isinstance(content, str) else json.dumps(content)


def make_research_batch_node(
    *,
    system_prompt: str,
    user_prompt: str,
    output_key: str,
    model: str = DEFAULT_PERPLEXITY_MODEL,
) -> Callable[[AgentState], AgentState]:
    """Build a node that runs a single Perplexity research call.

    The user prompt is .format()-ed with `company_name` taken from state.
    The raw assistant text is written to `state[output_key]`.
    """

    def node(state: AgentState) -> dict:
        company_name = state.get("company_name") or "Unknown"
        formatted = user_prompt.format(company_name=company_name)
        try:
            return {output_key: _perplexity_chat(system_prompt, formatted, model)}
        except Exception:
            return {output_key: ""}

    return node


def make_analyst_node(
    *,
    user_prompt: str,
    output_key: str,
    system_prompt: str | None = None,
    model: str = DEFAULT_ANALYST_MODEL,
    extra_inputs: dict[str, Callable[[AgentState], object]] | None = None,
    structured_output_model: type[BaseModel] | None = None,
) -> Callable[[AgentState], AgentState]:
    """Build a node that runs a single OpenAI analyst call.

    The user prompt is .format()-ed with:
      • company_name        — from state["company_name"]
      • research_data       — JSON-serialised state["research_data"]
      • citations           — JSON-serialised state["citations"]
      • plus anything in `extra_inputs` (callable taking state → value)
    """

    def node(state: AgentState) -> dict:
        ctx = {
            "company_name": state.get("company_name") or "Unknown",
            "research_data": json.dumps(state.get("research_data") or {}, indent=2),
            "citations": json.dumps(state.get("citations") or [], indent=2),
        }
        if extra_inputs:
            for key, getter in extra_inputs.items():
                ctx[key] = getter(state)

        formatted_user_prompt = user_prompt.format(**ctx)
        try:
            return {output_key: _openai_chat(
                user_prompt=formatted_user_prompt,
                model=model,
                system_prompt=system_prompt,
                output_model=structured_output_model,
            )}
        except Exception:
            return {output_key: ""}

    return node
