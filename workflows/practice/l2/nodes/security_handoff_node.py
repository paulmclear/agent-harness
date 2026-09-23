from workflows.practice.l2.state import State
from workflows.practice.l2.models import TriageOutput, SupportTicket, SupportCategory, SupportPriority


def security_handoff_node(state: State) -> str:
    """ Security handoffs require fields to be set deterministically """
    
    ticket: SupportTicket = state['ticket']
    
    triage_output = TriageOutput(
        ticket_id=ticket.ticket_id,
        needs_human_review=True,
        priority=SupportPriority.critical,
        priority_confidence=1.0,
        category=SupportCategory.security,
        category_confidence=1.0,
        assigned_team="Cyber Security Operations",
        assigned_team_confidence=1.0,
    )

    return {
        "triage_output": triage_output
    }
