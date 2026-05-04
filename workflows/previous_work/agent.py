from pprint import pprint

from dotenv import load_dotenv
from langchain.agents import create_agent

from tools.hubspot import search_hubspot_contact_by_email

load_dotenv()


agent = create_agent(
    model="openai:gpt-5.4-nano",
    tools=[search_hubspot_contact_by_email],
    system_prompt="You are a helpful assistant that provides information about contacts in our HubSpot CRM based on their email address.",
)


if __name__ == "__main__":
    # Example usage
    email_to_lookup = "craig.sangster@mbcl.com"

    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Find contact information for {email_to_lookup}"}]}
    )
    pprint(result["messages"][-1].content)
