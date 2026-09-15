"""Monitoring domain services and public engine exports."""

from . import services
from .services import (
    InvalidMonitoringConfiguration,
    MonitoringError,
    PingResult,
    latest_record,
    monitor_device,
    ping_ipv4,
    record_measurement,
)

# Keep the subprocess module reachable for existing monitoring-engine tests and
# integrations that patch the process runner through the public monitoring module.
subprocess = services.subprocess

__all__ = [
    "InvalidMonitoringConfiguration",
    "MonitoringError",
    "PingResult",
    "latest_record",
    "monitor_device",
    "ping_ipv4",
    "record_measurement",
]
