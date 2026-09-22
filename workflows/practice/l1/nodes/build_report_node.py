from workflows.practice.l1.state import State


def build_report_node(state: State) -> dict:
    """Assemble the final Markdown report.

    Part 1 is the established facts supplied to the analyst agent (customer record,
    rule-engine result, matched policies). Part 2 is the agent's assessment verbatim.
    """
    customer = state["customer"]
    risk = state["risk"]

    lines = [
        "# Customer Due Diligence Report",
        "",
        f"**Customer ID:** {state['customer_id']}",
        "",
        "---",
        "",
        "# Part 1 — Established Facts",
        "",
        "## Customer Record",
        "",
        *(f"- **{key}**: {value}" for key, value in customer.model_dump().items()),
        "",
        f"## Rule Engine Result: {risk.rating.upper()} (score {risk.score})",
        "",
    ]

    if risk.factors:
        lines += [f"- **{f.code}** (+{f.points}): {f.description}" for f in risk.factors]
    else:
        lines.append("No risk factors triggered.")
    lines.append("")

    if state.get("policy_chunks"):
        lines += ["## Matched Policies", ""]
        lines += [f"- **{p.id} – {p.title}**: {p.text}" for p in state["policy_chunks"]]
        lines.append("")

    lines += [
        "---",
        "",
        "# Part 2 — Analyst Risk Assessment",
        "",
        state["risk_assessment_output"].strip(),
        "",
    ]

    return {"report": "\n".join(lines)}
