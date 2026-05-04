# Input assumptions and edge-case handling

## Input assumptions

The workflow may receive any mix of:

- Calendar entry: title, date/time, organiser, attendee list, description.
- Previous meeting notes: minutes, decisions, action logs, internal notes, CRM notes.
- Recent email or message activity: client asks, internal concerns, follow-up requests, unresolved questions.
- Project or account status notes: RAID logs, status reports, delivery updates, milestones, issue trackers.
- Stakeholder information: roles, account ownership, stakeholder maps, known priorities or sensitivities.

Inputs may be incomplete, uneven, duplicative, stale, or contradictory.

## Source weighting

Treat signals as more important when they are:

1. Repeated across multiple source types.
2. Recent relative to the meeting date.
3. Client-facing or raised by a senior stakeholder.
4. Linked to decisions, ownership, budget, delivery dates, compliance, scope, trust, or relationship tone.
5. Explicitly marked as a RAID item, blocker, delay, concern, or unresolved action.

Treat signals as less important when they are:

- Old and not repeated recently.
- Purely administrative.
- Already resolved and not questioned by later sources.
- Speculative without supporting evidence.

## Contradictions

Do not choose one version silently. Surface the tension and make it actionable.

Pattern:

> [Issue] appears [resolved/advanced] in [source A], but [source B] suggests [continued concern/open question]. The meeting owner should confirm [status/owner/next step].

## Limited information

If only a calendar description and a few snippets are available:

- Produce a brief anyway.
- Mark confidence as low or medium where appropriate.
- Keep risks minimal unless the snippets clearly show concern.
- Include questions that fill the most important gaps.

## Missing attendee details

- Use names exactly as supplied.
- Include roles only if supplied or retrieved from reliable stakeholder records.
- If no role is available, write "role not provided" or omit the role field in JSON.

## No obvious risks

Use:

> No explicit material risks identified from the available inputs.

Do not create generic risks such as "alignment risk" or "communication risk" unless the evidence supports them.

## Too much raw information

- Cluster duplicated facts into themes.
- Prefer 3-5 high-value context bullets over exhaustive summaries.
- Do not include transcript-like chronology unless the user requests it.
