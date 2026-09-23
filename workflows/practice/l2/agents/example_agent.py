import textwrap

from workflows.practice.l2.agents._base import make_agent_node

SYSTEM_PROMPT = textwrap.dedent("""
    You are a concise research assistant. Answer only from what you know,
    say plainly when you are unsure, and never invent sources.
""").strip()

USER_PROMPT_TEMPLATE = textwrap.dedent("""
    Date: {current_date}

    Write a three-bullet brief on: {topic}
""").strip()

example_agent_node = make_agent_node(
    name="example_agent",
    system_prompt=SYSTEM_PROMPT,
    user_prompt_template=USER_PROMPT_TEMPLATE,
    output_state_key="example_agent_output",
)
