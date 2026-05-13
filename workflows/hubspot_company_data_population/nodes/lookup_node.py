from pprint import pprint

from dotenv import load_dotenv
from langchain.agents import create_agent

from tools.hubspot import search_hubspot_company_by_name

load_dotenv()


agent = create_agent(
    model="openai:gpt-5.4-nano",
    tools=[search_hubspot_company_by_name],
    system_prompt="You are a helpful assistant that provides information about companies in our HubSpot CRM based on their name.",
)


if __name__ == "__main__":
    # Example usage
    company_name_to_lookup = "Bank of Georgia"

    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Find company information for {company_name_to_lookup}"}]}
    )
    pprint(result["messages"][-1].content)
