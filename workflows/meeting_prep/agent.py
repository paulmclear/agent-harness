from typing import NotRequired, TypedDict
from pprint import pprint

from dotenv import load_dotenv
from deepagents import create_deep_agent
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from yaml import SafeLoader, load

from agents.meeting_prep.tools import (
    fetch_account_project_summary_status,
    fetch_prior_meeting_notes,
    fetch_recent_emails,
)

load_dotenv()

basic_model = ChatOpenAI(model="gpt-5.4-mini")
advanced_model = ChatOpenAI(model="gpt-5.4")


def load_prompt(name: str) -> str:
    prompts = {
        "meeting_planner_agent": "agents/meeting_prep/meeting_planner_system_prompt.txt",
        "plan_writeup_agent": "agents/meeting_prep/plan_writeup_system_prompt.txt",
    }
    with open(prompts[name], "r") as f:
        return f.read()


class MeetingDetails(TypedDict):
    title: str
    participants: list[str]
    calendar_description: str
    project_name: str


class MeetingBriefingOutput(TypedDict):
    meeting_purpose: str
    meeting_participants: list[str]
    key_recent_context: list[str]
    open_risk_and_issues: list[str]
    recommended_talking_points: list[str]
    recommended_follow_up_actions: list[str]
    questions_to_ask: list[str]


class AgentState(TypedDict):
    # input
    meeting_details: MeetingDetails
    # intermediate: synthesised analysis from meeting_planner_node
    analysis: NotRequired[str]
    # output
    meeting_briefing: NotRequired[MeetingBriefingOutput]


# Stage 1+2: deep agent calls the three data tools and synthesises the context
meeting_planner_agent = create_deep_agent(
    model="openai:gpt-5.4",
    tools=[
        fetch_account_project_summary_status,
        fetch_prior_meeting_notes,
        fetch_recent_emails,
    ],
    system_prompt=load_prompt("meeting_planner_agent"),
)

# Stage 3: structured-output chain — no tool loop needed, just format the analysis
plan_writeup_chain = basic_model.with_structured_output(MeetingBriefingOutput)


# nodes

def meeting_planner_node(state: AgentState) -> dict:
    """Call data tools and produce a synthesised meeting analysis."""
    meeting = state["meeting_details"]
    participants_str = (
        ", ".join(meeting["participants"]) if meeting["participants"] else "None provided"
    )
    user_prompt = (
        f"Prepare a meeting briefing for:\n"
        f"Title: {meeting['title']}\n"
        f"Project/Client: {meeting.get('project_name', meeting['title'])}\n"
        f"Participants: {participants_str}\n"
        f"Calendar Description: {meeting['calendar_description']}"
    )
    result = meeting_planner_agent.invoke(
        {"messages": [{"role": "user", "content": user_prompt}]}
    )
    return {"analysis": result["messages"][-1].content}


def plan_writeup_node(state: AgentState) -> dict:
    """Convert the meeting analysis into a structured MeetingBriefingOutput."""
    meeting = state["meeting_details"]
    participants_str = (
        ", ".join(meeting["participants"]) if meeting["participants"] else "None provided"
    )
    messages = [
        {"role": "system", "content": load_prompt("plan_writeup_agent")},
        {
            "role": "user",
            "content": (
                f"Meeting: {meeting['title']}\n"
                f"Participants: {participants_str}\n\n"
                f"{state.get('analysis', '')}"
            ),
        },
    ]
    briefing = plan_writeup_chain.invoke(messages)
    return {"meeting_briefing": briefing}


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("meeting_planner_node", meeting_planner_node)
    builder.add_node("plan_writeup_node", plan_writeup_node)

    builder.add_edge(START, "meeting_planner_node")
    builder.add_edge("meeting_planner_node", "plan_writeup_node")
    builder.add_edge("plan_writeup_ node", END)

    return builder.compile()


if __name__ == "__main__":
    with open("agents/meeting_prep/test_meetings.yaml", "r") as f:
        test_meetings = load(f, SafeLoader)

    test_meeting = test_meetings["test_meetings"][0]

    initial_state = {
        "meeting_details": {
            "title": test_meeting["title"],
            "participants": test_meeting["participants"],
            "calendar_description": test_meeting["calendar_description"],
            "project_name": test_meeting.get("project_name", test_meeting["title"]),
        },
    }

    workflow = build_graph()
    result = workflow.invoke(initial_state)

    pprint(result["meeting_briefing"])
