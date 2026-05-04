import cmd
import uuid
from pprint import pprint

from dotenv import load_dotenv
from langchain.messages import HumanMessage

from agents.researcher_agent import researcher_agent

load_dotenv()

class AgentShell(cmd.Cmd):
    intro = "Welcome to the Agent Shell. Type help or ? to list commands.\n"
    prompt = "(agent) "

    thread_id = str(uuid.uuid4())
    config={"configurable": {"thread_id": thread_id}}

    # def do_chat(self, arg):
    #     """Chat with the agent. Usage: chat <message>"""
    #     message = arg.strip()
    #     if not message:
    #         print("Please provide a message to chat.")
    #         return

    #     human_message = HumanMessage(content=message)
    #     result = agent.invoke({"messages": [human_message]}, config=self.config)
    #     pprint(result["messages"][-1].content)

    def do_research(self, arg):
        """Conduct research on a given topic. Usage: research <topic>"""
        topic = arg.strip()
        if not topic:
            print("Please provide a topic for research.")
            return

        message_research_task = HumanMessage(f"Conduct research on the following topic: {topic}")
        result = researcher_agent.invoke({"messages": [message_research_task]})
        pprint(result["messages"][-1].content)

    def do_exit(self, arg):
        """Exit the Agent Shell."""
        print("Goodbye!")
        return True

if __name__ == "__main__":
    AgentShell().cmdloop()
