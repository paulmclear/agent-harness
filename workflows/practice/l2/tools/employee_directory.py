from workflows.practice.l2.models import Employee


def get_employee(employee_id: str) -> Employee:
    """Retrieve an employee by their ID. - Placeholder implementation."""
    return Employee(
        employee_id=employee_id,
        name="Sarah Jones",
        department="Finance",
        office="London",
        email="sarah.jones@company.com",
        device_ids=["LT-2841"]
    )
