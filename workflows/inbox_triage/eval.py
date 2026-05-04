from typing import TypedDict, cast

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from yaml import SafeLoader, load

from agents.inbox_triage.agent import build_graph

load_dotenv()

judge_model = ChatOpenAI(model="gpt-5.4-mini")


class JudgeResult(TypedDict):
    classification_match: bool
    urgency_match: bool
    team_match: bool
    overall_pass: bool
    reasoning: str


def llm_judge(test_case: dict, actual: dict) -> JudgeResult:
    """Compare the triage agent's classification against the expected outcomes
    for a single test case and return a structured pass/fail judgment."""

    llm = judge_model.with_structured_output(JudgeResult)

    prompt = f"""
    <task>
    You are an evaluator scoring an inbox triage agent. For one test email,
    compare the actual classification produced by the agent against the
    expected values defined by the test author. Decide for each dimension
    whether the actual value satisfies the expectation, then give an overall
    verdict.
    </task>
    <matching_rules>
    - If an expected value lists alternatives joined by "or" (e.g. "medium or high"),
      the actual value passes if it matches any of the listed alternatives.
    - If the expected team is "n/a" (e.g. for spam where no team needs to handle it),
      treat the team dimension as automatically satisfied regardless of actual value.
    - String comparison should be case-insensitive and ignore surrounding whitespace.
    - overall_pass is true only if classification_match, urgency_match, and team_match
      are all true.
    - In `reasoning`, briefly explain any mismatches in one or two sentences.
    </matching_rules>
    <expected>
    classification: {test_case["expected_classification"]}
    urgency: {test_case["expected_urgency"]}
    team: {test_case["expected_team"]}
    </expected>
    <actual>
    classification: {actual["email_category"]}
    urgency: {actual["urgency"]}
    team: {actual["recommended_team"]}
    rationale: {actual["rationale"]}
    </actual>
    """.strip()

    return cast(JudgeResult, llm.invoke(prompt))


def run_tests():
    with open("agents/inbox_triage/test_emails.yaml", "r") as f:
        test_emails = load(f, SafeLoader)

    triage_workflow = build_graph()

    results = []
    for test_email in test_emails["test_emails"]:
        print(f"\n--- {test_email['scenario_name']} ---")

        initial_state = {
            "email_body": test_email["body"],
            "email_subject": test_email["subject"],
        }
        result = triage_workflow.invoke(initial_state)
        classification = result["classification"]

        judgment = llm_judge(test_email, classification)

        status = "PASS" if judgment["overall_pass"] else "FAIL"
        print(f"  status:   {status}")
        print(
            f"  expected: {test_email['expected_classification']} | "
            f"{test_email['expected_urgency']} | {test_email['expected_team']}"
        )
        print(
            f"  actual:   {classification['email_category']} | "
            f"{classification['urgency']} | {classification['recommended_team']}"
        )
        print(f"  reasoning: {judgment['reasoning']}")

        results.append({"scenario": test_email["scenario_name"], "judgment": judgment})

    passed = sum(1 for r in results if r["judgment"]["overall_pass"])
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{len(results)} passed")

    return results


if __name__ == "__main__":
    run_tests()
