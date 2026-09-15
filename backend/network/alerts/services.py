from ..models import FaultEvent, Notification


def create_fault_notification(fault: FaultEvent) -> Notification:
    notification, _ = Notification.objects.get_or_create(fault=fault)
    return notification


def mark_notification_read(notification: Notification) -> Notification:
    notification.status = Notification.Status.READ
    notification.save(update_fields=['status'])
    return notification
