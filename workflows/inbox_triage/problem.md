## Exercise 1 – Inbox Triage Agent

A good first exercise is to build something **small, useful, and realistic** without needing a huge orchestration design.

### Scenario

You work for a consulting firm. A shared mailbox receives incoming client emails. The business wants an agent that reads each email and decides:

* what type of email it is
* how urgent it is
* who should handle it
* whether a draft reply should be suggested

This is a strong beginner exercise because it teaches:

* structured outputs
* classification
* simple routing
* guardrails
* optional human review

---

## Business goal

Build an agent that takes an incoming email and returns a structured triage decision.

It should classify the email into one of these categories:

* `sales_lead`
* `client_request`
* `support_issue`
* `billing`
* `spam`
* `other`

It should also assign:

* urgency: `low`, `medium`, `high`
* recommended team: `sales`, `delivery`, `support`, `finance`, `operations`
* whether a human review is required: `true` or `false`
* a short rationale
* an optional draft reply

---

## Example input

```text
Subject: Urgent – access issue with Compass

Hi team,

We cannot access the Compass dashboard this morning and have a board meeting at 11am. Please can someone help as soon as possible?

Thanks,
Sarah
Head of Compliance
```

---

## Expected kind of output

```json
{
  "category": "support_issue",
  "urgency": "high",
  "recommended_team": "support",
  "human_review_required": true,
  "rationale": "The sender reports loss of access to a system and mentions a near-term board meeting, indicating a time-sensitive support issue.",
  "draft_reply": "Hi Sarah, thanks for letting us know. We are treating this as urgent and are looking into the access issue now. We will update you as soon as possible."
}
```

---

## Your task

Build **version 1** of this agent.

### Minimum requirements

1. Accept an email subject and body as input.
2. Return a **validated structured output**.
3. Use clear rules in the prompt for:

   * classification
   * urgency
   * when human review is required
4. Ensure spam or unclear emails are flagged conservatively.
5. Keep the rationale short, ideally one or two sentences.

---

## Suggested design

### If using PydanticAI

This is a very natural fit:

* define a Pydantic model for the output
* create one agent
* give it clear triage instructions
* validate the result

### If using LangGraph

Keep it simple:

* **Node 1**: classify and triage
* **Node 2**: if `human_review_required == true`, route to review
* **Node 3**: otherwise finalise output

For this first exercise, a full graph is optional. A single agent is enough.

---

## Edge cases to handle

Your agent should behave sensibly for these:

### 1. Ambiguous message

```text
Subject: Quick question

Hi, just wanted to ask about your services.
```

### 2. Spam

```text
Subject: Earn £5,000 per week from home
```

### 3. Billing issue

```text
Subject: Invoice discrepancy

Hello, the amount on invoice 1042 does not match the agreed fee.
```

### 4. Sensitive client complaint

```text
Subject: Formal complaint

We are unhappy with the quality of the recent deliverable and would like this escalated.
```

This last one should probably trigger `human_review_required = true`.

---

## What you are practising

By doing this well, you will learn:

* how to design a **useful output schema**
* how to write a prompt with **business rules**
* how to balance **automation vs escalation**
* how to think like a real business system designer rather than just “make an agent”

---

## Stretch goal

After version 1 works, add:

* confidence score
* SLA deadline suggestion
* recommended next action
* separate handling for complaints or legal risk

---

## Deliverable

Build the agent and test it on at least **5 sample emails**.

When you have done that, send me:

1. your schema
2. your prompt
3. your code
4. 2 or 3 sample outputs

I will then review it like a technical lead and give you the next exercise.
