"""Celery tasks for automated network monitoring."""

from __future__ import annotations

import logging
from datetime import timedelta

import redis
from celery import shared_task
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from .models import Device, MonitoringConfiguration, MonitoringRecord
from .monitoring import InvalidMonitoringConfiguration, monitor_device
from .snmp import SNMPMonitoringError, collect_snmp_metrics

logger = logging.getLogger(__name__)

MONITORING_DISPATCH_INTERVAL_SECONDS = 5
LOCK_TIMEOUT_SECONDS = 30 * 60


def _redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)


def _device_is_due(device: Device, now) -> bool:
    configuration = device.monitoring_configuration
    latest = MonitoringRecord.objects.filter(device=device).first()
    if latest is None:
        return True
    return latest.timestamp + timedelta(seconds=configuration.interval_seconds) <= now


@shared_task(
    bind=True,
    autoretry_for=(),
    retry_backoff=False,
    acks_late=True,
    time_limit=30 * 60,
)
def monitor_device_task(self, device_id: str) -> dict:
    """Monitor one device without blocking an HTTP request.

    The distributed Redis lock prevents overlapping monitoring runs for the
    same device when Celery workers or beat dispatches race with one another.
    """
    lock = _redis_client().lock(
        f"network-monitoring:device:{device_id}",
        timeout=LOCK_TIMEOUT_SECONDS,
        blocking=False,
    )

    if not lock.acquire():
        logger.info("Skipping overlapping monitoring task for device %s", device_id)
        return {"device_id": device_id, "status": "skipped", "reason": "already_running"}

    try:
        close_old_connections()
        try:
            device = Device.objects.select_related("monitoring_configuration").get(id=device_id)
        except Device.DoesNotExist:
            logger.warning("Monitoring task received unknown device %s", device_id)
            return {"device_id": device_id, "status": "skipped", "reason": "device_not_found"}

        if not device.monitoring_enabled:
            logger.info("Skipping disabled monitoring for device %s", device_id)
            return {"device_id": device_id, "status": "skipped", "reason": "monitoring_disabled"}

        result: dict = {"device_id": device_id, "status": "success", "snmp": None}

        try:
            record = monitor_device(device)
            result["monitoring_record_id"] = str(record.id)
            result["reachable"] = record.reachable
        except InvalidMonitoringConfiguration as exc:
            logger.warning("Monitoring configuration rejected for device %s: %s", device_id, exc)
            return {"device_id": device_id, "status": "configuration_error", "error": str(exc)}
        except Exception:
            logger.exception("ICMP monitoring failed for device %s", device_id)
            result["status"] = "partial"
            result["icmp_error"] = "ICMP monitoring failed."

        configuration = MonitoringConfiguration.objects.get(device=device)
        if configuration.snmp_enabled:
            try:
                snmp_result = collect_snmp_metrics(device)
                result["snmp"] = {
                    "status": snmp_result.status,
                    "metrics": len(snmp_result.metrics),
                    "errors": list(snmp_result.errors),
                }
                if snmp_result.status in {"error", "configuration_error"}:
                    result["status"] = "partial" if result["status"] == "success" else result["status"]
            except SNMPMonitoringError as exc:
                logger.warning("SNMP monitoring failed for device %s: %s", device_id, exc)
                result["status"] = "partial" if result["status"] == "success" else result["status"]
                result["snmp"] = {"status": "error", "metrics": 0, "errors": [str(exc)]}
            except Exception:
                logger.exception("Unexpected SNMP monitoring failure for device %s", device_id)
                result["status"] = "partial" if result["status"] == "success" else result["status"]
                result["snmp"] = {"status": "error", "metrics": 0, "errors": ["SNMP monitoring failed."]}

        logger.info("Completed monitoring for device %s with status %s", device_id, result["status"])
        return result
    finally:
        try:
            lock.release()
        except redis.exceptions.LockError:
            logger.warning("Monitoring lock for device %s expired before release", device_id)
        close_old_connections()


@shared_task

def dispatch_due_monitoring_tasks() -> dict:
    """Dispatch monitoring tasks for enabled devices whose interval elapsed."""
    now = timezone.now()
    dispatched = 0
    skipped = 0

    devices = Device.objects.filter(monitoring_enabled=True).select_related("monitoring_configuration")
    for device in devices.iterator():
        if not _device_is_due(device, now):
            continue
        monitor_device_task.delay(str(device.id))
        dispatched += 1

    logger.info("Dispatched %s due monitoring tasks; %s devices were not due", dispatched, skipped)
    return {"dispatched": dispatched}
