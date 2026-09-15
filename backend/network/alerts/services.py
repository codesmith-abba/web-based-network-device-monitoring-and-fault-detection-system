"""Notification services for detected network faults."""

from ..models import FaultEvent, Notification


NOTIFIABLE_SEVERITIES = frozenset({
    FaultEvent.Severity.HIGH,
    FaultEvent.Severity.CRITICAL,
})


def should_notify_fault(fault: FaultEvent) -> bool:
    """Return whether a detected fault should create a basic notification."""
    return fault.severity in NOTIFIABLE_SEVERITIES


def create_fault_notification(fault: FaultEvent) -> Notification | None:
    """Create one unread notification for a selected fault, if applicable."""
    if not should_notify_fault(fault):
        return None
    notification, _ = Notification.objects.get_or_create(fault=fault)
    return notification


def mark_notification_read(notification: Notification) -> Notification:
    notification.status = Notification.Status.READ
    notification.save(update_fields=['status'])
    return notification
