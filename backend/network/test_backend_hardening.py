from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Device, FaultEvent, MonitoringRecord, Notification
from .tasks import monitor_device_task


User = get_user_model()


class BackendWorkflowHardeningTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.device = Device.objects.create(
            name='Core Router',
            ip_address='192.168.1.1',
            device_type=Device.DeviceType.ROUTER,
        )

    def test_complete_high_latency_fault_workflow(self):
        from .monitoring import PingResult

        with patch('network.monitoring.services.ping_ipv4') as ping:
            ping.return_value = PingResult(True, 650.0, 0.0)
            response = self.client.post(
                f'/api/devices/{self.device.id}/monitor/',
                {},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
        )
        self.assertEqual(fault.severity, FaultEvent.Severity.HIGH)
        self.assertEqual(fault.status, FaultEvent.Status.ACTIVE)
        self.assertTrue(Notification.objects.filter(fault=fault).exists())

        response = self.client.post(f'/api/faults/{fault.id}/acknowledge/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], FaultEvent.Status.ACKNOWLEDGED)

        response = self.client.post(f'/api/faults/{fault.id}/resolve/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], FaultEvent.Status.RESOLVED)
        fault.refresh_from_db()
        self.assertIsNotNone(fault.resolved_at)

    def test_recovery_resolves_monitoring_fault(self):
        from .monitoring import PingResult

        with patch('network.monitoring.services.ping_ipv4') as ping:
            ping.return_value = PingResult(True, 700.0, 0.0)
            self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
            ping.return_value = PingResult(True, 20.0, 0.0)
            response = self.client.post(
                f'/api/devices/{self.device.id}/monitor/',
                {},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        fault = FaultEvent.objects.get(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
        )
        self.assertEqual(fault.status, FaultEvent.Status.RESOLVED)
        self.assertIsNotNone(fault.resolved_at)

    def test_monitoring_api_returns_404_for_unknown_device(self):
        response = self.client.get('/api/devices/00000000-0000-0000-0000-000000000000/monitoring-snapshot/')
        self.assertEqual(response.status_code, 404)

    def test_monitoring_summary_rejects_invalid_hours(self):
        response = self.client.get(f'/api/devices/{self.device.id}/monitoring-summary/?hours=abc')
        self.assertEqual(response.status_code, 400)
        self.assertIn('hours', response.data['detail'])

    def test_historical_api_rejects_reversed_date_range(self):
        start = timezone.now().isoformat()
        end = (timezone.now() - timedelta(hours=1)).isoformat()
        response = self.client.get(f'/api/monitoring-history/?from={start}&to={end}')
        self.assertEqual(response.status_code, 400)

    def test_historical_api_rejects_invalid_reachable_filter(self):
        response = self.client.get('/api/monitoring-history/?reachable=yes')
        self.assertEqual(response.status_code, 400)

    def test_fault_history_supports_filters_and_aggregation(self):
        now = timezone.now()
        FaultEvent.objects.create(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
            severity=FaultEvent.Severity.HIGH,
            detected_at=now - timedelta(hours=2),
        )
        response = self.client.get(
            f'/api/fault-history/?deviceId={self.device.id}&severity=high&aggregation=day'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['mode'], 'aggregated')
        self.assertGreaterEqual(len(response.data['buckets']), 1)


class CeleryIntegrationHardeningTests(APITestCase):
    def setUp(self):
        self.device = Device.objects.create(
            name='Worker Router',
            ip_address='10.0.0.1',
            device_type=Device.DeviceType.ROUTER,
        )

    def test_monitoring_task_uses_redis_lock_and_persists_result(self):
        lock = Mock()
        lock.acquire.return_value = True
        redis_client = Mock()
        redis_client.lock.return_value = lock

        record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=timezone.now(),
            reachable=True,
            latency_ms=10.0,
            packet_loss_percent=0.0,
        )

        with (
            patch('network.tasks._redis_client', return_value=redis_client),
            patch('network.tasks.monitor_device', return_value=record),
        ):
            result = monitor_device_task.run(str(self.device.id))

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['monitoring_record_id'], str(record.id))
        redis_client.lock.assert_called_once()
        lock.acquire.assert_called_once_with()
        lock.release.assert_called_once_with()

    def test_monitoring_task_skips_when_lock_is_held(self):
        lock = Mock()
        lock.acquire.return_value = False
        redis_client = Mock()
        redis_client.lock.return_value = lock

        with patch('network.tasks._redis_client', return_value=redis_client):
            result = monitor_device_task.run(str(self.device.id))

        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'already_running')


class SecurityContractHardeningTests(APITestCase):
    def test_protected_endpoints_require_authentication(self):
        paths = [
            '/api/devices/',
            '/api/dashboard/',
            '/api/monitoring-history/',
            '/api/fault-history/',
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 401)

    def test_authenticated_non_admin_is_forbidden(self):
        operator = User.objects.create_user(username='operator', password='operator123')
        token = Token.objects.create(user=operator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_health_check_remains_public(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'ok', 'database': 'ok'})

    def test_invalid_device_payload_returns_validation_error(self):
        user = User.objects.create_user(username='admin', password='admin123', is_staff=True)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.post(
            '/api/devices/',
            {
                'name': '',
                'ipAddress': 'not-an-ip',
                'type': 'invalid',
                'monitoring': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data)
        self.assertIn('ipAddress', response.data)
        self.assertIn('type', response.data)
