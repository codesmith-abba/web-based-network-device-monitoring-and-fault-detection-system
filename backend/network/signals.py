from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FaultEvent, Notification


@receiver(post_save, sender=FaultEvent)
def create_fault_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.get_or_create(fault=instance)
