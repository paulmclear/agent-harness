"""Customer system — a fake read-only backend backed by ``data/customers.yaml``."""

from workflows.practice.l1.tools._data import load
from workflows.practice.l1.tools.models import Customer


class CustomerNotFoundError(LookupError):
    pass


def get_customer_tool(customer_id: str) -> Customer:
    for record in load("customers.yaml"):
        if record["customer_id"] == customer_id:
            return Customer(**record)
    raise CustomerNotFoundError(f"No customer with id {customer_id!r}")
