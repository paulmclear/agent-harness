#!/usr/bin/env python3
"""Build a first-pass meeting briefing pack from a JSON input bundle.

This helper is intentionally lightweight. It is useful for demos, tests, and
structured inputs, but the main skill instructions should be used for nuanced
source retrieval, contradiction handling, and final editorial judgement.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

RISK_TERMS = {
    "risk", "delay", "delayed", "slippage", "concern", "issue", "open",
    "unresolved", "blocked", "blocker", "amber", "red", "awaiting", "disputed",
    "escalation", "sensitive", "ownership", "provisioning", "sign-off", "signoff",
}

STATUS_TERMS = {"fixed", "resolved", "deployed", "closed", "complete", "completed"}

SECTION_ORDER = [
    "meeting_purpose",
    "attendee_summary",
    "key_recent_context",
    "risks_or_open_issues",
    "recommended_talking_points",
    "questions_to_ask",
    "follow_up_actions",
]


def flatten_strings(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        text = value.strip()
        if text:
            yield text
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)


def normalise_topic(text: str) -> str:
    lowered = text.lower()
    topic_map = {
        "dashboard": "dashboard",
        "access": "access",
        "provision": "access",
        "phase 2": "phase 2",
        "timeline": "timeline",
        "target date": "timeline",
        "scope": "scope",
        "sign-off": "sign-off",
        "signoff": "sign-off",
        "ownership": "ownership",
        "owner": "ownership",
        "action": "actions",
        "raid": "raid",
    }
    for key, topic in topic_map.items():
        if key in lowered:
            return topic
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{3,}", lowered)
    return words[0] if words else "general"


def parse_attendee(raw: str) -> dict[str, str | None]:
    parts = re.split(r"\s+-\s+|\s+–\s+", raw, maxsplit=1)
    if len(parts) == 2:
        name, role = parts[0].strip(), parts[1].strip()
    else:
        name, role = raw.strip(), None
    org = None
    if role and "," in role:
        role_part, org_part = role.rsplit(",", 1)
        role, org = role_part.strip(), org_part.strip()
    return {"name": name, "role": role, "organisation": org}


def get_calendar(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("calendar_entry") or data.get("calendar") or {}


def collect_source_items(data: dict[str, Any]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for key, value in data.items():
        if key in {"calendar_entry", "calendar"}:
            continue
        for text in flatten_strings(value):
            items.append((key, text))
    return items


def bulletise(items: Iterable[str], limit: int = 5) -> list[str]:
    seen = set()
    out = []
    for item in items:
        compact = re.sub(r"\s+", " ", item.strip())
        key = compact.lower()
        if compact and key not in seen:
            out.append(compact)
            seen.add(key)
        if len(out) >= limit:
            break
    return out


def build_brief(data: dict[str, Any]) -> str:
    calendar = get_calendar(data)
    title = calendar.get("meeting_title") or calendar.get("title") or "Untitled meeting"
    description = calendar.get("meeting_description") or calendar.get("description") or ""
    participants = calendar.get("participants") or calendar.get("attendees") or []
    attendees = [parse_attendee(p) for p in participants if isinstance(p, str)]

    source_items = collect_source_items(data)
    all_texts = [text for _, text in source_items]

    topics: dict[str, list[str]] = defaultdict(list)
    for _, text in source_items:
        topics[normalise_topic(text)].append(text)

    repeated_topics = [topic for topic, values in topics.items() if len(values) > 1]
    risk_candidates = []
    resolved_by_topic: dict[str, list[str]] = defaultdict(list)
    concern_by_topic: dict[str, list[str]] = defaultdict(list)
    for text in all_texts:
        lowered = text.lower()
        topic = normalise_topic(text)
        if any(term in lowered for term in RISK_TERMS):
            risk_candidates.append(text)
            concern_by_topic[topic].append(text)
        if any(term in lowered for term in STATUS_TERMS):
            resolved_by_topic[topic].append(text)

    contradictions = []
    for topic in set(resolved_by_topic) & set(concern_by_topic):
        contradictions.append(
            f"{topic.capitalize()} may need confirmation: status notes suggest progress or resolution, "
            f"but other signals still show concern or an open question."
        )

    context_points = []
    for topic in repeated_topics:
        combined = "; ".join(bulletise(topics[topic], 3))
        context_points.append(f"{topic.capitalize()}: {combined}")
    context_points.extend(all_texts)
    context_points = bulletise(context_points, 5)

    risk_points = bulletise(contradictions + risk_candidates, 5)
    if not risk_points:
        risk_points = ["No explicit material risks identified from the available inputs."]

    purpose_basis = description or title
    purpose = (
        f"This appears to be about {purpose_basis.strip().rstrip('.')}."
        if purpose_basis else
        "The meeting purpose is not clear from the available inputs."
    )

    lines = [f"# Meeting Briefing Pack: {title}", ""]
    lines.extend(["## 1. Meeting purpose", purpose, ""])

    lines.append("## 2. Attendee summary")
    if attendees:
        for attendee in attendees:
            role = attendee["role"] or "role not provided"
            org = f", {attendee['organisation']}" if attendee.get("organisation") else ""
            lines.append(f"- **{attendee['name']}** - {role}{org}.")
    else:
        lines.append("- Attendee details are not clear from the available inputs.")
    lines.append("")

    lines.append("## 3. Key recent context")
    if context_points:
        lines.extend(f"- {point}" for point in context_points)
    else:
        lines.append("- No recent context was provided beyond the calendar entry.")
    lines.append("")

    lines.append("## 4. Risks or open issues")
    lines.extend(f"- {point}" for point in risk_points)
    lines.append("")

    talking_points = [
        "Confirm the current position on the most repeated or decision-relevant issues.",
        "Clarify owners, dates, and dependencies for any open actions.",
        "Acknowledge any client-raised concerns and explain the evidence for current status.",
    ]
    lines.append("## 5. Recommended talking points")
    lines.extend(f"- {point}" for point in talking_points)
    lines.append("")

    questions = [
        "What needs to be agreed in this meeting for the next step to proceed?",
        "Are there any open actions whose ownership or timing is unclear?",
        "Do the client and internal teams agree on the status of the key issues?",
    ]
    lines.append("## 6. Questions to ask")
    lines.extend(f"- {question}" for question in questions)
    lines.append("")

    actions = [
        "Capture agreed owners and due dates for open actions.",
        "Record any changes to risk, timeline, scope, or sign-off status.",
        "Send a concise follow-up confirming decisions, unresolved questions, and next steps.",
    ]
    lines.append("## 7. Follow-up actions")
    lines.extend(f"- {action}" for action in actions)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a first-pass meeting briefing pack from JSON input.")
    parser.add_argument("input_json", type=Path, help="Path to the input JSON bundle.")
    parser.add_argument("--output", "-o", type=Path, help="Optional output markdown path.")
    args = parser.parse_args()

    with args.input_json.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object at the top level.")

    brief = build_brief(data)
    if args.output:
        args.output.write_text(brief, encoding="utf-8")
    else:
        print(brief)


if __name__ == "__main__":
    main()
