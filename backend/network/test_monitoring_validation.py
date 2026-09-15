from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import FaultEvent, MonitoringRecord, Notification, SNMPMetric
from .monitoring import PingResult, monitor_device
from .snmp import SNMPMonitoringError, SNMPMetricResult, collect_snmp_metrics
from .tasks import monitor_device_task


User = get_user_model()


class NetworkMonitoringValidationTests(APITestCase):
    """Controlled/simulated validation scenarios for Phase 24."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="validation-admin",
            email="validation@example.com",
            password="validation123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/devices/",
            {
                "name": "Validation Router",
                "ipAddress": "192.0.2.20",
                "type": "router",
                "monitoring": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.device_id = response.data["id"]
        self.device = self._device()

    def _device(self):
        from .models import Device

        return Device.objects.get(id=self.device_id)

    def _monitor(self, result):
        with patch("network.monitoring.services.ping_ipv4", return_value=result):
            return monitor_device(self.device)

    def test_01_reachable_device(self):
        record = self._monitor(PingResult(True, 20.0, 0.0))

        self.device.refresh_from_db()
        self.assertTrue(record.reachable)
        self.assertEqual(record.latency_ms, 20.0)
        self.assertEqual(record.packet_loss_percent, 0.0)
        self.assertEqual(self.device.status, self.device.Status.ONLINE)
        self.assertFalse(FaultEvent.objects.filter(device=self.device).exists())

    def test_02_unreachable_device_creates_fault_and_notification(self):
        record = self._monitor(PingResult(False, None, 100.0, "simulated unreachable device"))

        self.device.refresh_from_db()
        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
        )
        self.assertFalse(record.reachable)
        self.assertEqual(self.device.status, self.device.Status.OFFLINE)
        self.assertEqual(fault.status, FaultEvent.Status.ACTIVE)
        self.assertTrue(Notification.objects.filter(fault=fault).exists())

    def test_03_high_latency_creates_fault(self):
        record = self._monitor(PingResult(True, 650.0, 0.0))

        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
        )
        self.assertEqual(record.latency_ms, 650.0)
        self.assertEqual(fault.severity, FaultEvent.Severity.HIGH)
        self.assertEqual(fault.status, FaultEvent.Status.ACTIVE)

    def test_04_packet_loss_creates_fault(self):
        record = self._monitor(PingResult(True, 50.0, 60.0))

        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_PACKET_LOSS,
        )
        self.assertEqual(record.packet_loss_percent, 60.0)
        self.assertEqual(fault.severity, FaultEvent.Severity.HIGH)
        self.assertEqual(fault.status, FaultEvent.Status.ACTIVE)

    def test_05_snmp_supported_device_persists_metrics(self):
        configuration = self.device.monitoring_configuration
        configuration.snmp_enabled = True
        configuration.snmp_version = "2c"
        configuration.snmp_community = "validation"
        configuration.available_metrics = ["sysName", "sysUpTime"]
        configuration.save()

        results = {
            "sysName": SNMPMetricResult("sysName", "1.3.6.1.2.1.1.5.0", "validation-router", "OctetString"),
            "sysUpTime": SNMPMetricResult("sysUpTime", "1.3.6.1.2.1.1.3.0", "12345", "TimeTicks"),
        }
        with patch("network.snmp.services._get_metric", side_effect=lambda *args: results[args[-1]]):
            result = collect_snmp_metrics(self.device)

        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.metrics), 2)
        self.assertEqual(SNMPMetric.objects.filter(device=self.device).count(), 2)

    def test_06_snmp_unavailable_device_is_isolated(self):
        configuration = self.device.monitoring_configuration
        configuration.snmp_enabled = True
        configuration.snmp_version = "2c"
        configuration.snmp_community = "validation"
        configuration.available_metrics = ["sysName"]
        configuration.save()

        with patch(
            "network.snmp.services._get_metric",
            side_effect=SNMPMonitoringError("simulated SNMP timeout"),
        ):
            result = collect_snmp_metrics(self.device)

        self.assertEqual(result.status, "error")
        self.assertEqual(len(result.metrics), 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(SNMPMetric.objects.filter(device=self.device).count(), 0)

    def test_07_repeated_monitoring_failure_persists_single_active_fault(self):
        failure = PingResult(False, None, 100.0, "simulated repeated failure")
        self._monitor(failure)
        first_fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
        )
        second = self._monitor(failure)

        active_faults = FaultEvent.objects.filter(
            device=self.device,
            fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
            status=FaultEvent.Status.ACTIVE,
        )
        self.assertEqual(MonitoringRecord.objects.filter(device=self.device).count(), 2)
        self.assertEqual(active_faults.count(), 1)
        self.assertEqual(active_faults.get().id, first_fault.id)
        self.assertFalse(second.reachable)

    def test_08_fault_persists_until_condition_recovers(self):
        self._monitor(PingResult(True, 650.0, 0.0))
        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
        )

        self._monitor(PingResult(True, 700.0, 0.0))
        fault.refresh_from_db()
        self.assertEqual(fault.status, FaultEvent.Status.ACTIVE)
        self.assertIsNone(fault.resolved_at)
        self.assertEqual(
            FaultEvent.objects.filter(
                device=self.device,
                fault_type=FaultEvent.FaultType.HIGH_LATENCY,
                status=FaultEvent.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_09_fault_resolves_after_healthy_measurement(self):
        self._monitor(PingResult(True, 650.0, 0.0))
        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
        )

        self._monitor(PingResult(True, 20.0, 0.0))
        fault.refresh_from_db()
        self.assertEqual(fault.status, FaultEvent.Status.RESOLVED)
        self.assertIsNotNone(fault.resolved_at)

    def test_10_historical_records_are_exposed(self):
        self._monitor(PingResult(True, 20.0, 0.0))
        self._monitor(PingResult(True, 650.0, 0.0))

        response = self.client.get(f"/api/monitoring-history/?deviceId={self.device_id}")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["meta"]["count"], 2)

        response = self.client.get(f"/api/fault-history/?deviceId={self.device_id}")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["meta"]["count"], 1)

    def test_11_dashboard_exposes_monitoring_fault_and_health_state(self):
        self._monitor(PingResult(True, 650.0, 0.0))

        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["totalDevices"], 1)
        self.assertEqual(response.data["summary"]["activeFaults"], 1)
        self.assertEqual(response.data["deviceHealth"][0]["latencyMs"], 650.0)

    def test_12_celery_task_handles_unavailable_snmp_as_partial_result(self):
        configuration = self.device.monitoring_configuration
        configuration.snmp_enabled = True
        configuration.snmp_version = "2c"
        configuration.snmp_community = "validation"
        configuration.available_metrics = ["sysName"]
        configuration.save()

        with patch("network.tasks._redis_client") as redis_client, patch(
            "network.tasks.collect_snmp_metrics",
        ) as collect:
            lock = redis_client.return_value.lock.return_value
            lock.acquire.return_value = True
            collect.return_value.status = "error"
            collect.return_value.metrics = ()
            collect.return_value.errors = ("simulated SNMP timeout",)

            with patch("network.monitoring.services.ping_ipv4", return_value=PingResult(True, 20.0, 0.0)):
                result = monitor_device_task.run(str(self.device.id))

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["snmp"]["status"], "error")
        self.assertEqual(result["snmp"]["metrics"], 0)
        lock.release.assert_called_once()
