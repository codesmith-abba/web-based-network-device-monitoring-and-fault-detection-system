"""ICMP-based monitoring engine.

All ping and persistence logic lives here rather than in API views so the
engine can be reused by a scheduler or background worker later.
"""

from __future__ import annotations

import ipaddress
import platform
import re
import subprocess
import time
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import Device, MonitoringConfiguration, MonitoringRecord


DEFAULT_PING_TIMEOUT_SECONDS = 2.0
_LATENCY_PATTERN = re.compile(r"time[=<]([0-9]+(?:[.,][0-9]+)?)\s*ms", re.IGNORECASE)


class MonitoringError(Exception):
    """Base exception for expected monitoring errors."""


class InvalidMonitoringConfiguration(MonitoringError):
    """Raised when a device cannot be monitored with its configuration."""


@dataclass(frozen=True)
class PingResult:
    reachable: bool
    latency_ms: float | None
    packet_loss_percent: float
    error: str | None = None


def _validate_ipv4(address: str) -> None:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise InvalidMonitoringConfiguration("Device IP address is invalid.") from exc

    if parsed.version != 4:
        raise InvalidMonitoringConfiguration("ICMP monitoring currently supports IPv4 devices only.")


def _ping_command(address: str, timeout_seconds: float) -> list[str]:
    system = platform.system().lower()
    timeout_ms = max(1, int(timeout_seconds * 1000))

    if system == "windows":
        return ["ping", "-n", "1", "-w", str(timeout_ms), address]
    if system == "darwin":
        return ["ping", "-n", "-c", "1", "-W", str(timeout_ms), address]
    return ["ping", "-n", "-c", "1", "-W", str(max(1, int(timeout_seconds))), address]


def _parse_latency(output: str) -> float | None:
    match = _LATENCY_PATTERN.search(output)
    if match is None:
        return None
    return float(match.group(1).replace(",", "."))


def ping_ipv4(address: str, timeout_seconds: float = DEFAULT_PING_TIMEOUT_SECONDS) -> PingResult:
    """Execute one bounded ICMP echo request without invoking a shell."""
    _validate_ipv4(address)

    if timeout_seconds <= 0:
        raise InvalidMonitoringConfiguration("Ping timeout must be greater than zero.")

    command = _ping_command(address, timeout_seconds)
    started = time.monotonic()

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds + 0.5,
        )
    except subprocess.TimeoutExpired:
        return PingResult(False, None, 100.0, "ICMP request timed out.")
    except FileNotFoundError:
        return PingResult(False, None, 100.0, "The system ping utility is not available.")
    except OSError as exc:
        return PingResult(False, None, 100.0, f"ICMP network error: {exc}")

    output = f"{completed.stdout}\n{completed.stderr}"
    latency = _parse_latency(output)

    if completed.returncode == 0:
        if latency is None:
            latency = round((time.monotonic() - started) * 1000, 3)
        return PingResult(True, latency, 0.0)

    return PingResult(False, None, 100.0, "Device is unreachable or did not respond to ICMP.")


def _get_configuration(device: Device) -> MonitoringConfiguration:
    configuration, _ = MonitoringConfiguration.objects.get_or_create(device=device)
    if configuration.interval_seconds < 5:
        raise InvalidMonitoringConfiguration("Monitoring interval must be at least 5 seconds.")
    return configuration


@transaction.atomic
def monitor_device(device: Device) -> MonitoringRecord:
    """Ping a device once and persist its reachability/latency result.

    Expected network failures become an unreachable record instead of an
    exception, so a failed device cannot crash the web application.
    Configuration errors are raised explicitly for the API to report safely.
    """
    if not device.monitoring_enabled:
        raise InvalidMonitoringConfiguration("Monitoring is disabled for this device.")

    _get_configuration(device)
    result = ping_ipv4(str(device.ip_address))

    record = MonitoringRecord.objects.create(
        device=device,
        timestamp=timezone.now(),
        reachable=result.reachable,
        latency_ms=result.latency_ms,
        packet_loss_percent=result.packet_loss_percent,
    )

    new_status = Device.Status.ONLINE if result.reachable else Device.Status.OFFLINE
    if device.status != new_status:
        device.status = new_status
        device.save(update_fields=["status", "updated_at"])

    return record
