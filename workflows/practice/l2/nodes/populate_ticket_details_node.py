from workflows.practice.l2.models import SupportTicket
from workflows.practice.l2.tools.employee_directory import get_employee
from workflows.practice.l2.tools.device_catalogue import get_device
from workflows.practice.l2.state import State


def populate_ticket_details_node(state: State) -> dict:
    """ For a given ticket, locate the employee and their devices """

    ticket: SupportTicket = state["ticket"]

    # fetch employee
    employee = get_employee(employee_id=ticket.employee_id)

    # fetch devices
    employee_devices = [
        get_device(device_id=device_id)
        for device_id in employee.device_ids
    ]

    return {
        "employee": employee,
        "devices": employee_devices,
    }
