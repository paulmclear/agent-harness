import datetime as dt
from typing import Sequence

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from workflows.practice.l1.state import State


DEFAULT_MODEL = "openai:gpt-5.4"


def get_user_prompt(template: str, state: State) -> str:
    # formats the user prompt template with the current date and state values
    return template.format(
        current_date=dt.datetime.now().strftime("%Y-%m-%d"),
        **state,
    )


def make_agent_node(
    *,
    name: str,
    system_prompt: str,
    user_prompt_template: str,
    output_state_key: str,
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
        tools=list(tools) if tools else None,
    )

    def node(state: State) -> dict:
        
        user_prompt = get_user_prompt(user_prompt_template, state)
        
        if state.get("debug"):
            print("User prompt:\n", user_prompt)
            output = ""
        else:
            response = agent.invoke(
                {"messages": [HumanMessage(content=user_prompt)]}
            )
            output = response["messages"][-1].content
        
        return {
            output_state_key: output
        }

    return node
