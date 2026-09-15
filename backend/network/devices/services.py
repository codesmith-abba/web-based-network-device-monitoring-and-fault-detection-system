from ..models import Device, MonitoringConfiguration


def ensure_monitoring_configuration(device: Device) -> MonitoringConfiguration:
    configuration, _ = MonitoringConfiguration.objects.get_or_create(device=device)
    return configuration
