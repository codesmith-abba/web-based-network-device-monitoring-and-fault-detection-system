from django.utils import timezone

from ..models import Device, MonitoringRecord


def latest_record(device: Device) -> MonitoringRecord | None:
    return device.monitoring_records.first()


def record_measurement(
    device: Device,
    *,
    reachable: bool | None,
    latency_ms: float | None = None,
    packet_loss_percent: float | None = None,
    timestamp=None,
) -> MonitoringRecord:
    return MonitoringRecord.objects.create(
        device=device,
        timestamp=timestamp or timezone.now(),
        reachable=reachable,
        latency_ms=latency_ms,
        packet_loss_percent=packet_loss_percent,
    )
