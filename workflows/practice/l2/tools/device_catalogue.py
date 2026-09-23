from workflows.practice.l2.models import Device


def get_device(device_id: str) -> Device:
    """Retrieve a device by its ID. - Placeholder implementation."""
    return Device(
        device_id=device_id,
        os="Windows 10",
        managed=True,
        last_seen="2026-09-01T12:00:00Z"
    )
