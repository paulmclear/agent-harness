## Exercise 2 – Meeting Briefing Agent

This is the next right step because it introduces:

* **multiple inputs**
* **light orchestration**
* **tool-like data sources**
* **structured synthesis**
* **clear separation between deterministic steps and agentic steps**

It is still manageable, but more realistic than inbox triage.

---

# Scenario

A manager has a client meeting later today. They want an agent workflow that prepares a **meeting briefing pack** from a few inputs.

The workflow receives:

* the meeting title
* meeting participants
* calendar description
* notes from prior meetings
* recent email snippets
* account or project status notes

The system should produce a concise briefing that helps the manager walk into the meeting prepared.

---

# Business goal

Build an agent workflow that generates a **structured meeting briefing** with the most important context, risks, and suggested talking points.

The briefing should include:

* meeting purpose
* who the attendees are
* key recent context
* open issues or risks
* recommended talking points
* recommended follow-up actions
* questions that should be asked in the meeting

---

# Example input

```json id="uh747w"
{
  "meeting_title": "Quarterly Compass Steering Committee",
  "participants": [
    "Sarah Ahmed – Head of Compliance, ClientCo",
    "Tom Willis – Programme Manager, ClientCo",
    "Paul McLear – Director, Plenitude"
  ],
  "calendar_description": "Quarterly steering committee to review Compass rollout progress, outstanding issues, and next phase priorities.",
  "previous_meeting_notes": [
    "Client requested improved dashboard filtering.",
    "Access provisioning delays affected two business users.",
    "Phase 2 delivery plan to be agreed by end of month."
  ],
  "recent_email_snippets": [
    "Client asked whether dashboard access issues are now fully resolved.",
    "Tom mentioned concern about slippage against the Phase 2 target date.",
    "Sarah wants a clearer view of ownership for open actions."
  ],
  "project_status_notes": [
    "Dashboard filtering enhancement is in UAT.",
    "Access issue fix deployed last week.",
    "Phase 2 scope still awaiting sign-off.",
    "Open RAID item: delivery timeline risk rated amber."
  ]
}
```

---

# Expected output shape

```json id="wgw0p3"
{
  "meeting_purpose": "Review Compass rollout progress, resolve outstanding issues, and align on Phase 2 priorities.",
  "attendee_summary": [
    "Sarah Ahmed – senior client stakeholder focused on compliance outcomes and action ownership.",
    "Tom Willis – programme manager likely focused on timeline and delivery confidence.",
    "Paul McLear – provider representative expected to guide status, risks, and next steps."
  ],
  "key_context": [
    "Dashboard filtering enhancement is currently in UAT.",
    "The access issue fix was deployed last week, but the client is still seeking assurance.",
    "Phase 2 scope remains unsigned, creating delivery uncertainty."
  ],
  "risks_and_open_issues": [
    "Timeline risk for Phase 2 remains amber.",
    "Client confidence may be affected if access issues are not clearly evidenced as resolved.",
    "Ownership of open actions may still appear unclear."
  ],
  "recommended_talking_points": [
    "Confirm current status of the access issue and provide evidence of resolution.",
    "Walk through dashboard filtering progress and expected release timing.",
    "Agree ownership and timeline for Phase 2 sign-off."
  ],
  "questions_to_ask": [
    "Are there any remaining user access issues in practice since the fix was deployed?",
    "What level of confidence do you have in the proposed Phase 2 scope?",
    "Which open actions need clearer ownership from either side?"
  ],
  "follow_up_actions": [
    "Send a written action log with owners and deadlines.",
    "Confirm UAT completion timing for dashboard filtering.",
    "Escalate unresolved scope sign-off risk if decision is delayed."
  ]
}
```

---

# Your task

Build a workflow that produces this structured briefing.

---

## Minimum requirements

### 1. Use a structured output schema

Define a schema for the final briefing.

### 2. Split the work into at least **three logical stages**

For example:

* **Node 1** – normalise and combine raw inputs
* **Node 2** – extract key themes, issues, and signals
* **Node 3** – generate the final briefing

### 3. Include at least one **deterministic rule**

Examples:

* if no risks are found, explicitly return an empty list
* if participant list is empty, state that attendee context is unavailable
* if an issue appears in both emails and project notes, treat it as more important

### 4. Keep the final briefing concise

Assume the output is for a busy manager who will read it in 2 minutes.

---

# What makes this exercise more advanced

Compared with the inbox exercise, this one adds:

* multiple heterogeneous inputs
* synthesis across sources
* signal prioritisation
* more nuanced output structure
* more obvious value from staged orchestration

---

# Real business behaviours to model

Your agent should notice patterns like:

* an issue mentioned in **multiple places** is probably important
* email tone can signal stakeholder concern even if project notes sound calm
* unresolved ownership is often a genuine delivery risk
* a meeting brief should not be a data dump – it should be selective

---

# Edge cases to test

## Case 1 – Thin inputs

Very little information is provided. The briefing should remain useful without inventing detail.

## Case 2 – Conflicting signals

Project notes say a problem is fixed, but recent emails show the client is still worried.

## Case 3 – No participants

The system should not hallucinate attendee roles.

## Case 4 – No clear risks

The output should say that no explicit risks were identified from the provided material.

---

# Deliverable

When you are done, send me:

1. your schema
2. your graph design
3. your prompt(s)
4. your code
5. one worked example output

I will review it against a new rubric, slightly stricter than the first one.

## Optional stretch

After you finish the main version, add a **quality-check node** that tests whether the final briefing is:

* concise
* non-duplicative
* grounded only in the provided inputs

That would be a very good next step.
