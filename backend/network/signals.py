from django.db.models.signals import post_save
from django.dispatch import receiver

from .alerts.services import create_fault_notification
from .models import FaultEvent


@receiver(post_save, sender=FaultEvent)
def create_fault_notification_signal(sender, instance, created, **kwargs):
    """Create a notification only when the fault meets notification policy."""
    if created:
        create_fault_notification(instance)
