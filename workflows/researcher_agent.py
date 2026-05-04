from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver

from tools.search_tool import internet_search

load_dotenv()


# System prompt to steer the agent to be an expert researcher
research_instructions = SystemMessage("""You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
""")

checkpointer = MemorySaver()


researcher_agent = create_deep_agent(
    model="openai:gpt-5-mini",
    backend=FilesystemBackend(root_dir='./sandbox/', virtual_mode=True),
    tools=[internet_search],
    system_prompt=research_instructions,
    checkpointer=checkpointer,
)

message_research_task = HumanMessage("""## Your Task
    Create a report on Agent Harnesses. Your report should cover the following aspects:
    - What are agent harnesses and how do they work?
    - What are the benefits of using agent harnesses?
    - What are some real-world applications of agent harnesses?
    
    ## Process Steps
    1. Write down a research plan to answer the question. Include at least 3 sub-questions that you need to answer to complete your research.
    2. For each sub-question, use the `internet_search` tool to gather information.
    3. After gathering information for all sub-questions, write a comprehensive report that answers the main question. Make sure to synthesize the information you found and provide a clear, concise answer to the main question.
    4. Output the report in markdown format using the file system."""
)

result = agent.invoke({"messages": [message_research_task]})

# Print the agent's response
print(result["messages"][-1].content)