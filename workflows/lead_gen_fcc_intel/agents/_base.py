import datetime as dt
from typing import Callable, Sequence

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from workflows.lead_gen_fcc_intel.state import AgentState

DEFAULT_MODEL = "openai:gpt-5.4"


def make_analyst_node(
    *,
    name: str,
    system_prompt: str,
    user_prompt: str,
    data_sources: dict[str, Callable[[], str]],
    output_key: str,
    tools: Sequence = (),
    model: str = DEFAULT_MODEL,
):
    """Build a LangGraph node that runs an analyst agent.

    The node fetches each data source, formats `user_prompt` with the results
    plus `current_date`, invokes the agent, and writes the assistant's final
    message text to `state[output_key]`.
    """
    agent = create_agent(
        name=name,
        system_prompt=system_prompt,
        model=model,
        tools=list(tools),
    )

    def node(state: AgentState) -> AgentState:
        fetched = {key: fetch() for key, fetch in data_sources.items()}
        formatted = user_prompt.format(
            current_date=dt.datetime.now().strftime("%Y-%m-%d"),
            **fetched,
        )
        output = agent.invoke({"messages": [HumanMessage(content=formatted)]})
        state[output_key] = output["messages"][-1].content
        return state

    return node
