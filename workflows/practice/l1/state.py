from typing import TypedDict

from workflows.practice.l1.tools import Customer, PolicyChunk, RiskAssessment


class State(TypedDict):
    
    # control
    debug: bool

    # input data
    customer_id: str

    # derived data
    customer: Customer
    risk: RiskAssessment
    policy_chunks: list[PolicyChunk]

    risk_assessment_output: str
    risk_assessment_qa_output: dict

    # output data
    report: str
    file_path: str
