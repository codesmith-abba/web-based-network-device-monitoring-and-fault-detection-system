from django.utils import timezone

from ..models import FaultEvent


def acknowledge_fault(fault: FaultEvent) -> FaultEvent:
    if fault.status == FaultEvent.Status.RESOLVED:
        raise ValueError('Resolved faults cannot be acknowledged.')
    fault.status = FaultEvent.Status.ACKNOWLEDGED
    fault.save(update_fields=['status'])
    return fault


def resolve_fault(fault: FaultEvent) -> FaultEvent:
    fault.status = FaultEvent.Status.RESOLVED
    fault.resolved_at = timezone.now()
    fault.save(update_fields=['status', 'resolved_at'])
    return fault
