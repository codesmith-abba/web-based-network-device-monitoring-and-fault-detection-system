"""SNMP monitoring domain services.

The Phase 15 implementation intentionally supports SNMPv1/v2c only. Devices
without SNMP support, disabled agents, invalid credentials, and unavailable
MIB objects are treated as monitoring outcomes rather than application errors.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from ..faults.detection import evaluate_snmp_metric
from ..models import Device, MonitoringConfiguration, SNMPMetric


SUPPORTED_METRICS = {
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'ifNumber': '1.3.6.1.2.1.2.1.0',
}
DEFAULT_METRICS = tuple(SUPPORTED_METRICS)


class SNMPMonitoringError(Exception):
    """Base exception for configuration-level SNMP errors."""


@dataclass(frozen=True)
class SNMPMetricResult:
    metric: str
    oid: str
    value: str
    value_type: str


@dataclass(frozen=True)
class SNMPResult:
    status: str
    metrics: tuple[SNMPMetricResult, ...]
    errors: tuple[str, ...]


def get_supported_metrics() -> dict[str, str]:
    return dict(SUPPORTED_METRICS)


def _validate_configuration(configuration: MonitoringConfiguration) -> None:
    if not configuration.snmp_enabled:
        raise SNMPMonitoringError('SNMP monitoring is disabled for this device.')
    if configuration.snmp_version not in {'1', '2c'}:
        raise SNMPMonitoringError('Only SNMPv1 and SNMPv2c are supported.')
    if not configuration.snmp_community:
        raise SNMPMonitoringError('An SNMP community is required when SNMP is enabled.')
    if not 1 <= configuration.snmp_port <= 65535:
        raise SNMPMonitoringError('SNMP port must be between 1 and 65535.')
    if configuration.snmp_timeout_seconds <= 0:
        raise SNMPMonitoringError('SNMP timeout must be greater than zero.')


def _selected_metrics(configuration: MonitoringConfiguration) -> list[str]:
    configured = configuration.available_metrics or list(DEFAULT_METRICS)
    return [metric for metric in configured if metric in SUPPORTED_METRICS]


async def _get_metric_async(
    address: str,
    port: int,
    community: str,
    version: str,
    timeout_seconds: float,
    metric: str,
) -> SNMPMetricResult:
    from pysnmp.hlapi.v3arch.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        get_cmd,
    )

    auth = CommunityData(community, mpModel=0 if version == '1' else 1)
    target = await UdpTransportTarget.create(
        (address, port),
        timeout=timeout_seconds,
        retries=0,
    )
    error_indication, error_status, error_index, var_binds = await get_cmd(
        SnmpEngine(),
        auth,
        target,
        ContextData(),
        ObjectType(ObjectIdentity(SUPPORTED_METRICS[metric])),
        lookupMib=False,
    )

    if error_indication:
        raise SNMPMonitoringError(str(error_indication))
    if error_status:
        index = int(error_index) - 1 if error_index else 0
        oid = SUPPORTED_METRICS[metric]
        if var_binds and 0 <= index < len(var_binds):
            oid = str(var_binds[index][0])
        raise SNMPMonitoringError(f'SNMP agent rejected {metric} ({oid}): {error_status}')
    if not var_binds:
        raise SNMPMonitoringError(f'SNMP agent returned no value for {metric}.')

    returned_oid, returned_value = var_binds[0]
    return SNMPMetricResult(
        metric=metric,
        oid=str(returned_oid),
        value=str(returned_value),
        value_type=type(returned_value).__name__,
    )


def _get_metric(
    address: str,
    port: int,
    community: str,
    version: str,
    timeout_seconds: float,
    metric: str,
) -> SNMPMetricResult:
    return asyncio.run(
        _get_metric_async(address, port, community, version, timeout_seconds, metric)
    )


def collect_snmp_metrics(device: Device) -> SNMPResult:
    """Poll configured SNMP metrics and persist successful values only."""
    configuration = MonitoringConfiguration.objects.get_or_create(device=device)[0]

    try:
        _validate_configuration(configuration)
    except SNMPMonitoringError as exc:
        return SNMPResult('disabled' if not configuration.snmp_enabled else 'configuration_error', (), (str(exc),))

    metrics = _selected_metrics(configuration)
    if not metrics:
        return SNMPResult('configuration_error', (), ('No supported SNMP metrics are configured.',))

    collected: list[SNMPMetricResult] = []
    errors: list[str] = []
    timestamp: datetime = timezone.now()

    for metric in metrics:
        try:
            result = _get_metric(
                str(device.ip_address),
                configuration.snmp_port,
                configuration.snmp_community or '',
                configuration.snmp_version or '2c',
                configuration.snmp_timeout_seconds,
                metric,
            )
        except Exception as exc:  # noqa: BLE001 - SNMP failures must stay isolated.
            errors.append(f'{metric}: {exc}')
            continue

        collected.append(result)
        stored_metric = SNMPMetric.objects.create(
            device=device,
            timestamp=timestamp,
            metric=result.metric,
            oid=result.oid,
            value=result.value,
            value_type=result.value_type,
        )
        evaluate_snmp_metric(stored_metric)

    if collected and errors:
        status = 'partial'
    elif collected:
        status = 'success'
    else:
        status = 'error'

    return SNMPResult(status, tuple(collected), tuple(errors))
