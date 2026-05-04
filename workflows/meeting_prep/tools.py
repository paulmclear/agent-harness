from pathlib import Path
import yaml
from langchain_core.tools import tool

_DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> dict:
    with open(_DATA_DIR / filename, "r") as f:
        return yaml.safe_load(f)


@tool
def fetch_prior_meeting_notes(client_or_project_name: str) -> str:
    """Retrieve notes from all prior meetings for the given client or project.

    Use this to understand what was discussed previously, what commitments were made,
    and what action items are outstanding before preparing a meeting briefing.

    Args:
        client_or_project_name: The name of the client or project to look up,
            e.g. 'Compass', 'DataBridge Migration', 'Synergy CRM'.
    """
    data = _load("meeting_notes.yaml")
    sessions = data.get(client_or_project_name)
    if not sessions:
        return f"No prior meeting notes found for '{client_or_project_name}'."

    lines = [f"Prior meeting notes for {client_or_project_name}:\n"]
    for session in sessions:
        lines.append(f"── {session['date']} | {session['type']} ──")
        lines.append(f"Attendees: {', '.join(session['attendees'])}")
        lines.append("Key points:")
        for point in session["key_points"]:
            lines.append(f"  • {point}")
        lines.append("Action items:")
        for action in session["action_items"]:
            lines.append(f"  • {action}")
        if session.get("decisions"):
            lines.append("Decisions:")
            for decision in session["decisions"]:
                lines.append(f"  • {decision}")
        lines.append("")

    return "\n".join(lines)


@tool
def fetch_recent_emails(client_or_project_name: str) -> list[str]:
    """Retrieve recent email threads related to the given client or project.

    Use this to surface stakeholder tone, escalations, unresolved concerns, or
    commitments made outside of formal meetings that should inform the briefing.

    Args:
        client_or_project_name: The name of the client or project to look up,
            e.g. 'Compass', 'DataBridge Migration', 'Synergy CRM'.
    """
    data = _load("emails.yaml")
    emails = data.get(client_or_project_name)
    if not emails:
        return [f"No recent emails found for '{client_or_project_name}'."]

    return [
        f"[{e['date']}] From: {e['from']} | Subject: {e['subject']}\n{e['snippet'].strip()}"
        for e in emails
    ]


@tool
def fetch_account_project_summary_status(client_or_project_name: str) -> str:
    """Retrieve the current account or project status for the given client or project.

    Use this to understand delivery health (RAG status), milestone progress, open risks
    and issues, RAID log items, and financial position before preparing a meeting briefing.

    Args:
        client_or_project_name: The name of the client or project to look up,
            e.g. 'Compass', 'DataBridge Migration', 'Synergy CRM'.
    """
    data = _load("project_status.yaml")
    status = data.get(client_or_project_name)
    if not status:
        return f"No project status found for '{client_or_project_name}'."

    lines = [
        f"Project: {status.get('programme', client_or_project_name)}",
        f"Client: {status.get('client', 'Unknown')}",
        f"Overall RAG: {status['overall_rag']}",
        f"Last updated: {status['last_updated']}",
        "",
        f"Summary: {status['summary'].strip()}",
        "",
        "Milestones:",
    ]
    for m in status.get("milestones", []):
        date_str = m.get("date") or m.get("target_date") or m.get("original_date", "TBC")
        lines.append(f"  • [{m['status']}] {m['name']} ({date_str})")

    raid = status.get("raid", {})
    risks = raid.get("risks", [])
    issues = raid.get("issues", [])

    if risks:
        lines.append("")
        lines.append("Risks:")
        for r in risks:
            lines.append(f"  • [{r['rating']}] {r['id']}: {r['description']}")
            lines.append(f"    Mitigation: {r['mitigation']}")

    if issues:
        lines.append("")
        lines.append("Open issues:")
        for i in issues:
            lines.append(f"  • [{i['status']}] {i['id']}: {i['description']}")

    findings = status.get("findings_summary")
    if findings:
        lines.append("")
        lines.append(
            f"Security findings: {findings['critical']} critical, {findings['high']} high, "
            f"{findings['medium']} medium, {findings['low']} low, "
            f"{findings['informational']} informational. "
            f"Overall posture: {findings['overall_posture']}."
        )

    fin = status.get("financials", {})
    if fin:
        lines.append("")
        lines.append(
            f"Financials: Contract {fin.get('contract_value', 'N/A')}, "
            f"invoiced {fin.get('invoiced_to_date', 'N/A')}, "
            f"{fin.get('outstanding_change_requests', 0)} outstanding CRs "
            f"({fin.get('cr_value_pending', '£0')} pending approval)."
        )

    return "\n".join(lines)
