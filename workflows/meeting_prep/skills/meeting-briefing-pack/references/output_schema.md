# Output schema

## Human-readable briefing template

```markdown
# Meeting Briefing Pack: [meeting title]

## 1. Meeting purpose
[1-3 sentences. Explain what the meeting appears to be about. Use cautious language where evidence is limited.]

## 2. Attendee summary
- **[Name]** – [role/title if known]. [Why they matter, if supported.]
- **Unknown / not provided** – [use only where attendee information is missing.]

## 3. Key recent context
- [Prioritised recent development, with source grounding where available.]
- [Repeated signals should appear before isolated signals.]

## 4. Risks or open issues
- [Material unresolved/sensitive issue, including contradiction or confidence qualifier where relevant.]
- [If none: "No explicit material risks identified from the available inputs."]

## 5. Recommended talking points
- [Practical point the meeting owner should cover.]

## 6. Questions to ask
- [Specific question that resolves ambiguity, confirms ownership, or moves the meeting forward.]

## 7. Follow-up actions
- [Likely next step to capture after the meeting.]
```

## JSON schema

Use this structure when the user requests machine-readable output or an API-style response:

```json
{
  "meeting_title": "string | null",
  "meeting_datetime": "string | null",
  "briefing_generated_from": [
    {
      "source_type": "calendar | meeting_notes | email | project_status | stakeholder_info | crm | issue_tracker | other",
      "source_label": "string",
      "date_or_recency": "string | null"
    }
  ],
  "meeting_purpose": {
    "summary": "string",
    "confidence": "high | medium | low",
    "basis": ["string"]
  },
  "attendee_summary": [
    {
      "name": "string",
      "organisation": "string | null",
      "role": "string | null",
      "relevance": "string | null",
      "confidence": "high | medium | low"
    }
  ],
  "key_recent_context": [
    {
      "point": "string",
      "source_signals": ["string"],
      "importance": "high | medium | low"
    }
  ],
  "risks_or_open_issues": [
    {
      "issue": "string",
      "why_it_matters": "string",
      "status": "open | unclear | disputed | sensitive | delayed | resolved_but_needs_confirmation",
      "source_signals": ["string"]
    }
  ],
  "recommended_talking_points": ["string"],
  "questions_to_ask": ["string"],
  "follow_up_actions": ["string"],
  "known_gaps_or_uncertainties": ["string"]
}
```

## Length and prioritisation defaults

- Keep the standard briefing to 350-700 words.
- Limit each section to 3-5 bullets unless the user asks for depth.
- Put repeated, current, client-facing, and decision-relevant signals first.
- Include known gaps only when they affect meeting preparation.
