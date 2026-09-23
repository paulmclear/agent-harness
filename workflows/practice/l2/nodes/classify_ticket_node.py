import logging

from typesafe_sdk import Choice, TypeSafeClient

from workflows.practice.l2.models import SupportCategory, SupportPriority
from workflows.practice.l2.state import State

logger = logging.getLogger(__name__)


CATEGORY_CRITERIA: dict[SupportCategory, str] = {
    SupportCategory.vpn: (
        "Connecting to or staying connected to the corporate VPN, VPN client "
        "errors, or remote access that goes through the VPN."
    ),
    SupportCategory.email: (
        "Sending, receiving, or syncing email, mailboxes, calendars, "
        "distribution lists, or the mail client itself."
    ),
    SupportCategory.hardware: (
        "Physical devices: laptops, monitors, docks, keyboards, phones, "
        "printers, or a device that is broken, damaged, lost, or needs replacing."
    ),
    SupportCategory.software: (
        "Installing, updating, licensing, or errors in an application or the "
        "operating system, excluding the VPN client and email client."
    ),
    SupportCategory.identity: (
        "Accounts and access: passwords, MFA, lockouts, SSO, permissions, or "
        "requests to grant or revoke access to a system."
    ),
    SupportCategory.network: (
        "Office Wi-Fi, wired network, internet connectivity, or DNS problems "
        "that are not specific to the VPN."
    ),
    SupportCategory.other: "An IT request that fits none of the other categories.",
}

PRIORITY_CRITERIA: dict[SupportPriority, str] = {
    SupportPriority.critical: (
        "Major outage or critical issue affecting multiple users or systems."
    ),
    SupportPriority.high: (
        "Significant issue including security incidents affecting a single user or a small group of users, but not a major outage."
    ),
    SupportPriority.normal: (
        "Normal issue affecting a single user, not causing significant disruption."
    ),
    SupportPriority.low: (
        "Feedback or minor issue with minimal impact."
    )
}


def classify_ticket_node(state: State) -> dict:
    """Classify a support ticket's category and priority in one TypeSafe call."""

    questions = {
        "ticket_category": Choice(
            instructions=(
                "Which IT support category best describes the main issue the "
                "employee raises in `ticket`?"
            ),
            criteria={
                category.value: description
                for category, description in CATEGORY_CRITERIA.items()
            },
        ),
        "ticket_priority": Choice(
            instructions=(
                "What is the priority level of the issue described in `ticket`?"
            ),
            criteria={
                priority.value: description
                for priority, description in PRIORITY_CRITERIA.items()
            },
        ),
    }

    with TypeSafeClient() as client:
        response = client.system_one(
            state={"ticket": state["ticket"]}, questions=questions
        )

    category_answer = response.choices["ticket_category"]
    priority_answer = response.choices["ticket_priority"]
    
    # Convert the raw choice strings to their respective enum types.
    category = SupportCategory(category_answer.choice)
    priority = SupportPriority(priority_answer.choice)

    logger.info(
        "Ticket category: %s (confidence %.2f), priority: %s (confidence %.2f)",
        category.value,
        category_answer.confidence,
        priority.value,
        priority_answer.confidence,
    )

    return {
        "ticket_category": category,
        "ticket_category_confidence": category_answer.confidence,
        "ticket_priority": priority,
        "ticket_priority_confidence": priority_answer.confidence,
    }
