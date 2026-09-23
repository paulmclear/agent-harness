from workflows.practice.l1.state import State


def write_report_to_file_node(state: State) -> dict:
    report = state["report"]
    file_path = f"report_{state['customer_id']}.md"
    with open(file_path, "w") as f:
        f.write(report)
    return {"file_path": file_path}
