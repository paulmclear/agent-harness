---
name: meeting-briefing-pack
description: create concise, grounded meeting briefing packs for upcoming client or account meetings from calendar details, meeting notes, emails, project/account status notes, raid logs, crm entries, issue trackers, and stakeholder information. use when the user asks for a meeting brief, client briefing pack, pre-meeting context, steering committee prep, account meeting summary, or an agent workflow that prepares meeting owners by identifying purpose, attendees, recent context, risks, talking points, questions, and follow-up actions while handling incomplete or contradictory source material.
---

# Meeting Briefing Pack

## Purpose

Produce a short, high-quality briefing that helps a busy manager or director prepare for an important meeting in a couple of minutes. The brief must be selective, action-oriented, and grounded in the supplied or retrieved source material. It is not a transcript, evidence dump, or generic account summary.

## Workflow

1. **Collect inputs**
   - Use the user-provided material first.
   - When the user asks for a brief for a real upcoming meeting and connectors are available, retrieve relevant calendar, email, CRM, project, document, and issue/status records before drafting.
   - Prefer recent and meeting-specific material over broad historical context.
   - Keep source provenance for claims, especially risks, contradictions, and recommended actions.

2. **Classify and normalise source signals**
   - Calendar: meeting title, date/time, organiser, description, attendees.
   - Prior notes: decisions, open actions, unresolved asks, carried-forward issues.
   - Emails/messages: client concerns, internal concerns, recent asks, tone, follow-ups.
   - Status/account notes: milestones, delivery progress, RAID items, scope, ownership, dependencies.
   - Stakeholder information: role, influence, ownership, sensitivities, priorities.

3. **Infer only what is supported**
   - State what the meeting appears to be about, using cautious language when evidence is thin.
   - Do not invent attendee roles, client sentiment, risks, actions, ownership, dates, or statuses.
   - If information is missing, say it is not clear from the available inputs.

4. **Prioritise materiality**
   - Promote issues repeated across sources.
   - Surface contradictions explicitly, for example: "internal notes say the access fix was deployed, but the client is still asking whether access is fully resolved".
   - Include risks only when they are material, unresolved, sensitive, disputed, delayed, or likely to affect the meeting outcome.
   - Do not turn every uncertainty into a risk.

5. **Draft the briefing**
   - Use the required structure in `references/output_schema.md`.
   - Keep the brief concise: usually 350-700 words, shorter when source material is limited.
   - Use bullets where they improve scanability.
   - Make talking points, questions, and follow-up actions practical and meeting-ready.

6. **Quality check before responding**
   - Verify every specific claim is grounded in an input or cited source.
   - Check that contradictions are not smoothed over.
   - Remove generic filler, repeated points, and low-value background.
   - Confirm the brief can be read quickly by a senior meeting owner.

## Output rules

Always include these sections in this order unless the user requests a different format:

1. Meeting purpose
2. Attendee summary
3. Key recent context
4. Risks or open issues
5. Recommended talking points
6. Questions to ask
7. Follow-up actions

Use "No explicit material risks identified from the available inputs" when no material risks are visible. Use "Not clear from the available inputs" rather than guessing.

For structured or programmatic outputs, use the JSON schema in `references/output_schema.md`.

## Connector guidance

When retrieving data from connected systems:

- Calendar: start from the exact meeting title, organiser, attendees, and date/time.
- Email/messages: search recent messages involving the client, project/account name, meeting title, and attendees. Focus on the last 30-60 days unless the user specifies otherwise.
- Project/account status: search project workspaces, RAID logs, status reports, action logs, CRM/account notes, issue trackers, and previous meeting notes.
- Stakeholders: use explicit titles or account ownership records only. Do not infer seniority from email tone or name alone.

When sources conflict, include the tension and explain why it matters for the meeting.

## Bundled resources

- `references/output_schema.md` – required markdown and JSON output structure.
- `references/input_assumptions.md` – data assumptions, source weighting, and edge-case handling.
- `references/prompts.md` – reusable system, retrieval, synthesis, and quality-check prompts.
- `scripts/build_brief.py` – optional deterministic helper that turns a JSON input bundle into a first-pass briefing draft for testing or demonstrations.
- `examples/sample_input.json` and `examples/sample_output.md` – sample input and expected style.
