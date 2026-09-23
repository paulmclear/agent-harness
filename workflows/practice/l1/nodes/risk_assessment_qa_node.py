"""
Verify the agent's assessment — after risk_assessment, before build_report
- Problem: report trusts free-form Markdown. The parsing alternative (regex ## Recommended Rating for Low/Medium/High) is exactly the fragile code to avoid.
- Judgments over {inputs, assessment}, all in one batched call:
  - Choice recommended rating → low / medium / high / unclear
  - Noul agrees with rule engine?
  - Noul every Evidence line cites only facts present in the inputs? (citation-check cookbook)
  - Noul Risk Assessment section follows Statement/Evidence/Analysis?
- Code owns policy: rating ≠ rule engine or grounding noul low → retry or route to human.


state = {
    "inputs": None, # use dicts
    "assessment": None
}

questions={
    "rating": Choice(
        instructions="Which risk rating does the assessment recommend?",
        criteria={"low": None, "medium": None, "high": None, "unclear": None}
    ),
    "agrees_with_engine": Noul(
        instructions="Does the assessment's rating match inputs.risk.rating?",
        criteria={
            "true": "The assessment's rating matches inputs.risk.rating.",
            "false": "The assessment's rating does not match inputs.risk.rating."
        }
    ),
    "grounded": Noul(
        instructions="Do the Evidence lines cite only facts present in the inputs?",
        criteria={
            "true": "All Evidence lines cite only facts present in the inputs.",
            "false": "One or more Evidence lines cite facts not present in the inputs."
        }
    ),
    "sea_structure": Noul(
        instructions="Does the Risk Assessment section follow the Statement/Evidence/Analysis structure?",
        criteria={
            "true": "The Risk Assessment section follows the Statement/Evidence/Analysis structure.",
            "false": "The Risk Assessment section does not follow the Statement/Evidence/Analysis structure."
        }
    )
}

"""

from typesafe_sdk import TypeSafeClient, Choice, Noul
from dotenv import load_dotenv

from workflows.practice.l1.state import State

load_dotenv()


def risk_assessment_qa_node(state: State) -> dict:

    agent_input = {
        "inputs": {
            "customer": state["customer"].model_dump(),
            "risk_calculation": state["risk"].model_dump(),
            "policy_chunks": [f.model_dump() for f in state["policy_chunks"]],
        },
        "risk_assessment": state["risk_assessment_output"]
    }

    with TypeSafeClient() as client:
        response = client.system_one(
            state=agent_input,
            questions={
                "rating": Choice(
                    instructions="Which risk rating does the assessment recommend?",
                    criteria={"low": None, "medium": None, "high": None, "unclear": None}
                ),
                # "agrees_with_engine": Noul(
                #     instructions="Does the assessment's rating match inputs.risk.rating?",
                #     criteria={
                #         "true": "The assessment's rating matches inputs.risk.rating.",
                #         "false": "The assessment's rating does not match inputs.risk.rating."
                #     }
                # ),
                "grounded": Noul(
                    instructions="Do the Evidence lines cite only facts present in the inputs?",
                    criteria={
                        "true": "All Evidence lines cite only facts present in the inputs.",
                        "false": "One or more Evidence lines cite facts not present in the inputs."
                    }
                ),
                "sea_structure": Noul(
                    instructions="Does the Risk Assessment section follow the Statement/Evidence/Analysis structure?",
                    criteria={
                        "true": "The Risk Assessment section follows the Statement/Evidence/Analysis structure.",
                        "false": "The Risk Assessment section does not follow the Statement/Evidence/Analysis structure."
                    }
                ),
            }
        )

    return {
        "risk_assessment_qa_output": dict(response)
    }
