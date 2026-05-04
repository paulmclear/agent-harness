from typing import TypedDict, Literal
from pprint import pprint

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from yaml import SafeLoader, load

load_dotenv()

basic_model = ChatOpenAI(model="gpt-5.4-mini")
# advanced_model = ChatOpenAI(model="gpt-5.4")


# define state
class EmailClassification(TypedDict):
    email_category: Literal[
        "sales_lead", "client_request", "support_issue", "billing", "spam", "other"
    ]
    urgency: Literal["low", "medium", "high"]
    recommended_team: Literal["sales", "delivery", "support", "finance", "operations"]
    human_review_required: bool
    rationale: str


class AgentState(TypedDict):
    # input data
    email_subject: str
    email_body: str
    email_sender: str

    # classification
    classification: EmailClassification

    # response
    draft_reply: str


def format_email_for_prompt(email_subject: str, email_body: str) -> str:
    return f"""
    <email_subject>
    {email_subject}
    </email_subject>
    <email_body>
    {email_body}
    </email_body>
    """.strip()


def format_classification_for_prompt(classification: EmailClassification):
    return f"""
    <email_category>
    {classification['email_category']}
    </email_category>
    <urgency>
    {classification['urgency']}
    </urgency>
    <recommended_team>
    {classification['recommended_team']}
    </recommended_team>
    <human_review_required>
    {classification['human_review_required']}
    </human_review_required>
    """.strip()



# agent 1 - classifier
def classify_email_agent(state: AgentState) -> Command:

    # create the model that returns the structured output
    llm = basic_model.with_structured_output(EmailClassification)

    # prompt
    prompt = f"""
    <task>
    You are an inbox triage assistant for a consulting firm. Analyse the email below
    and return a structured classification decision.
    </task>

    <classification_rules>
    Assign exactly one category using these definitions in priority order:
    - spam: unsolicited bulk mail, phishing, marketing you did not request, or clearly irrelevant messages
    - billing: invoice queries, payment disputes, or financial discrepancies
    - support_issue: a technical system, access, or operational problem requiring resolution
    - client_request: any communication from an existing client — including complaints, escalations,
      legal notices, deliverable submissions, change requests, or follow-ups on past work.
      If the email references a past engagement, project, invoice, or deliverable, treat the sender
      as an existing client and use this category.
    - sales_lead: an unsolicited enquiry from a prospect or unknown sender about services or pricing
    - other: genuinely does not fit any of the above after careful consideration

    When in doubt, prefer the more specific category over "other". Only use "other" if no
    other category fits after applying the rules above.
    </classification_rules>

    <urgency_rules>
    Default to "low". Only escalate when there is clear evidence:
    - high: the email explicitly mentions a hard deadline, an imminent meeting or event,
      a live system outage, a formal complaint, legal action, or regulatory/reputational risk
    - medium: a response is clearly expected but no specific time pressure is stated —
      e.g. a client asking for a change, a billing query, or a sales enquiry with real intent
    - low: everything else — vague enquiries, informational updates, routine submissions, spam

    Err toward lower urgency. An ambiguous or brief email with no time signal is low, not medium.
    Spam is always low.
    </urgency_rules>

    <team_rules>
    Route to the team best placed to resolve the email:
    - sales: sales_lead enquiries
    - delivery: client_request for work or deliverables
    - support: support_issue or access problems
    - finance: billing disputes or invoice queries
    - operations: internal process issues or ambiguous operational matters
    </team_rules>

    <human_review_rules>
    Set human_review_required to true if any of the following apply:
    - the email is a formal complaint or expresses strong dissatisfaction
    - the email mentions legal action, regulatory concerns, or reputational risk
    - urgency is high and the issue is time-sensitive (e.g. imminent meeting or outage)
    - the category or intent is genuinely ambiguous and a wrong decision would cause harm
    Spam never requires human review.
    </human_review_rules>

    <rationale_rules>
    Write a rationale of one or two sentences. Explain why you chose the category,
    urgency, and whether human review is needed. Be specific — reference the email content.
    </rationale_rules>

    {format_email_for_prompt(state['email_subject'], state['email_body'])}
    """.strip()

    # Get structured response directly as dict
    classification = llm.invoke(prompt)

    return Command(
        update={"classification": classification},
    )


# agent 2 - draft response based on classification
def draft_response_agent(state: AgentState) -> Command:

    prompt = f"""
    <task>
    You are drafting a reply on behalf of a consulting firm's shared mailbox.
    Write a professional, concise response to the email below based on the triage
    classification provided. Do not resolve the issue yourself — acknowledge it,
    set expectations, and confirm who will follow up.
    </task>

    <tone_guidelines>
    - Professional but warm; match the formality of the original email
    - Keep it to 3–5 sentences unless the email genuinely requires more
    - Address the sender by name if it is clear from the email
    - Do not make commitments you cannot guarantee (e.g. specific fix times)
    - If urgency is high, open with acknowledgement of the time sensitivity
    </tone_guidelines>

    <classification>
    {format_classification_for_prompt(state['classification'])}
    </classification>

    {format_email_for_prompt(state['email_subject'], state['email_body'])}
    """.strip()
    
    model_response = basic_model.invoke(prompt)
    draft_reply = model_response.content  # Assuming the model returns the draft reply in the content field

    return Command(
        update={"draft_reply": draft_reply},
    )


def classification_to_drafter_router(state: AgentState) -> str:
    """Route to the draft_response_agent if the email is not classified as spam and does not require human review."""
    classification = state["classification"]
    if classification["email_category"] == "spam" or classification["human_review_required"]:
        return END  # end the workflow, no draft needed
    return "draft_response_agent"  # route to drafting agent


def build_graph(output_image: bool = False) -> StateGraph[AgentState]:
    workflow_builder = StateGraph(AgentState)

    # nodes
    workflow_builder.add_node("classify_email_agent", classify_email_agent)
    workflow_builder.add_node("draft_response_agent", draft_response_agent)

    # edges
    workflow_builder.add_edge(START, "classify_email_agent")
    workflow_builder.add_conditional_edges(
        "classify_email_agent",
        classification_to_drafter_router,
        ["draft_response_agent", END],
    )
    workflow_builder.add_edge("draft_response_agent", END)

    # compile
    workflow = workflow_builder.compile()

    # output image of the graph
    if output_image:
        with open("agents/inbox_triage/triage_graph.png", "wb") as f:
            f.write(workflow.get_graph(xray=True).draw_mermaid_png())

    return workflow


if __name__ == "__main__":
    with open("agents/inbox_triage/test_emails.yaml", "r") as f:
        test_emails = load(f, SafeLoader)

    test_email = test_emails["test_emails"][0]

    initial_state = {
        "email_body": test_email["body"],
        "email_subject": test_email["subject"],
    }

    # build workflow and invoke
    workflow = build_graph(output_image=True)
    # result = workflow.invoke(initial_state)

    # pprint(result)
