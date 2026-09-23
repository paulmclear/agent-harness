import logging

from typesafe_sdk import TypeSafeClient

from workflows.practice.l2.models import SecurityAssessment, SecurityReason
from workflows.practice.l2.state import State

logger = logging.getLogger(__name__)


SECURITY_THRESHOLD = 0.6

REASON_CRITERIA: dict[SecurityReason, str] = {
    SecurityReason.phishing: (
        "The employee received, opened, or acted on a suspicious email, message, "
        "call, or link trying to trick them into giving access or information."
    ),
    SecurityReason.malware: (
        "A device shows signs of infection: unknown software, pop-ups, "
        "ransomware notes, antivirus alerts, or files being encrypted or changed."
    ),
    SecurityReason.lost_stolen_device: (
        "A laptop, phone, security key, or other device holding company data "
        "is lost, stolen, or missing."
    ),
    SecurityReason.compromised_account: (
        "An account shows signs someone else is using it: unexpected MFA "
        "prompts, logins the employee did not make, changed settings, or "
        "shared or leaked credentials."
    ),
    SecurityReason.data_exposure: (
        "Company or customer data was sent, shared, or made visible to someone "
        "who should not have it."
    ),
    SecurityReason.vulnerability: (
        "A system is unpatched, misconfigured, or exposed in a way that could "
        "be exploited, with no sign it has been exploited yet."
    ),
    SecurityReason.other: "A security concern that fits none of the other reasons.",
}


def classify_security_risk_node(state: State) -> dict:
    """Classify the security risk of a given ticket."""

    inputs = {"ticket": state["ticket"]}
    questions = {
        "has_security_implications": {
            "type": "noul",
            "instructions": (
                "Does the issue in `ticket` suggest a possible threat to the "
                "company's accounts, devices, systems, or data?"
            ),
            "criteria": {
                "true": (
                    "Signs of phishing, malware, a lost or stolen device, an "
                    "account used by someone else, data sent to the wrong "
                    "people, or an exploitable weakness. Include cases where "
                    "the employee is only unsure whether something was "
                    "malicious."
                ),
                "false": (
                    "Routine IT work with no sign of a threat, such as a "
                    "forgotten password, an expired password, a new access "
                    "request, a broken device that is still in the employee's "
                    "hands, or a slow or failing application."
                ),
            },
        },
        "security_reason_classification": {
            "type": "choice",
            "instructions": (
                "If the issue in `ticket` has security implications, what is "
                "the most likely cause?"
            ),
            "criteria": {
                reason.value: description
                for reason, description in REASON_CRITERIA.items()
            },
        },
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=inputs, questions=questions)

    security_probability = response.nouls["has_security_implications"].noul

    if security_probability > SECURITY_THRESHOLD:
        reason = response.choices["security_reason_classification"]
        security_assessment = SecurityAssessment(
            security_related=True,
            security_probability=security_probability,
            reason=SecurityReason(reason.choice),
            reason_confidence=reason.confidence,
        )
    else:
        security_assessment = SecurityAssessment(
            security_probability=security_probability
        )

    logger.info("Security assessment: %s", security_assessment)

    return {"security_assessment": security_assessment}


def requires_security_escalation(state: State) -> str:
    """Route to security handoff, or on to ticket classification."""
    if state["security_assessment"].security_related:
        return "security_handoff"
    return "classify_ticket"
