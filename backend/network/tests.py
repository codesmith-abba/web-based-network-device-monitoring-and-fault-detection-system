from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .faults.detection import evaluate_monitoring_record
from .models import Device, FaultEvent, MonitoringConfiguration, MonitoringRecord, Notification
from .monitoring import InvalidMonitoringConfiguration, PingResult, monitor_device


User = get_user_model()


class NetworkApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.device = Device.objects.create(
            name='Router 1',
            ip_address='192.168.1.1',
            device_type=Device.DeviceType.ROUTER,
            status=Device.Status.ONLINE,
        )

    def test_devices_list_uses_frontend_contract(self):
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'Router 1')
        self.assertEqual(response.data[0]['ipAddress'], '192.168.1.1')
        self.assertEqual(response.data[0]['type'], 'router')
        self.assertEqual(response.data[0]['monitoring'], True)

    def test_device_create_creates_monitoring_configuration(self):
        response = self.client.post('/api/devices/', {
            'name': 'Switch 1',
            'ipAddress': '192.168.1.2',
            'type': 'switch',
            'monitoring': True,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        created = Device.objects.get(id=response.data['id'])
        self.assertEqual(created.device_type, Device.DeviceType.SWITCH)
        self.assertTrue(hasattr(created, 'monitoring_configuration'))

    def test_device_rejects_invalid_ip_address(self):
        response = self.client.post('/api/devices/', {
            'name': 'Invalid Device',
            'ipAddress': 'not-an-ip',
            'type': 'router',
            'monitoring': True,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('ipAddress', response.data)

    def test_device_rejects_ipv6_address(self):
        response = self.client.post('/api/devices/', {
            'name': 'IPv6 Device',
            'ipAddress': '2001:db8::1',
            'type': 'router',
            'monitoring': True,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('ipAddress', response.data)

    def test_device_rejects_invalid_device_type(self):
        response = self.client.post('/api/devices/', {
            'name': 'Invalid Type',
            'ipAddress': '192.168.1.3',
            'type': 'printer',
            'monitoring': True,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('type', response.data)

    def test_device_can_be_retrieved_updated_and_deleted(self):
        response = self.client.get(f'/api/devices/{self.device.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'router')

        response = self.client.patch(
            f'/api/devices/{self.device.id}/',
            {'name': 'Core Router', 'type': 'firewall'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertEqual(self.device.name, 'Core Router')
        self.assertEqual(self.device.device_type, Device.DeviceType.FIREWALL)

        response = self.client.delete(f'/api/devices/{self.device.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Device.objects.filter(id=self.device.id).exists())
        self.assertFalse(MonitoringConfiguration.objects.filter(device_id=self.device.id).exists())

    def test_device_management_requires_administrator(self):
        operator = User.objects.create_user(username='operator', password='operator123')
        token = Token.objects.create(user=operator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, 403)

        self.client.credentials()
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, 401)

    def test_monitoring_snapshot_returns_latest_and_history(self):
        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=timezone.now() - timedelta(minutes=1),
            reachable=True,
            latency_ms=12.5,
            packet_loss_percent=0,
        )
        response = self.client.get(f'/api/devices/{self.device.id}/monitoring-snapshot/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['latest'])
        self.assertEqual(response.data['latest']['latencyMs'], 12.5)
        self.assertIn('configuration', response.data)

    @patch('network.monitoring.services.ping_ipv4')
    def test_monitor_endpoint_records_reachable_device_and_latency(self, mock_ping):
        mock_ping.return_value = PingResult(True, 8.4, 0.0)
        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['reachable'])
        self.assertEqual(response.data['latencyMs'], 8.4)
        self.assertEqual(response.data['packetLossPercent'], 0.0)
        record = MonitoringRecord.objects.get(device=self.device)
        self.assertTrue(record.reachable)
        self.assertEqual(record.latency_ms, 8.4)
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.ONLINE)

    @patch('network.monitoring.services.ping_ipv4')
    def test_monitor_endpoint_records_unreachable_device_without_crashing(self, mock_ping):
        mock_ping.return_value = PingResult(False, None, 100.0, 'ICMP request timed out.')
        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['reachable'])
        self.assertIsNone(response.data['latencyMs'])
        self.assertEqual(response.data['packetLossPercent'], 100.0)
        record = MonitoringRecord.objects.get(device=self.device)
        self.assertFalse(record.reachable)
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.OFFLINE)

    @patch('network.monitoring.services.ping_ipv4')
    def test_monitor_endpoint_handles_system_ping_failure(self, mock_ping):
        mock_ping.return_value = PingResult(False, None, 100.0, 'The system ping utility is not available.')
        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['reachable'])
        self.assertEqual(MonitoringRecord.objects.filter(device=self.device).count(), 1)

    def test_monitor_rejects_disabled_monitoring_configuration(self):
        self.device.monitoring_enabled = False
        self.device.save(update_fields=['monitoring_enabled'])
        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('disabled', response.data['detail'])
        self.assertFalse(MonitoringRecord.objects.filter(device=self.device).exists())

    def test_monitor_rejects_invalid_monitoring_interval(self):
        configuration = MonitoringConfiguration.objects.get(device=self.device)
        configuration.interval_seconds = 1
        configuration.save(update_fields=['interval_seconds'])
        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('at least 5 seconds', response.data['detail'])
        self.assertFalse(MonitoringRecord.objects.filter(device=self.device).exists())

    def test_monitoring_records_are_exposed_through_api(self):
        record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=timezone.now(),
            reachable=True,
            latency_ms=15.25,
            packet_loss_percent=0,
        )
        response = self.client.get(f'/api/monitoring-records/?deviceId={self.device.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], str(record.id))
        self.assertEqual(response.data[0]['latencyMs'], 15.25)

    def test_monitoring_endpoint_requires_administrator(self):
        operator = User.objects.create_user(username='operator', password='operator123')
        token = Token.objects.create(user=operator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_monitoring_endpoint_preserves_configuration_association(self):
        response = self.client.patch(
            f'/api/devices/{self.device.id}/monitoring/',
            {'monitoring': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertFalse(self.device.monitoring_enabled)
        self.assertTrue(MonitoringConfiguration.objects.filter(device=self.device).exists())

    def test_fault_creation_is_monitoring_controlled(self):
        response = self.client.post('/api/faults/', {
            'device': str(self.device.id),
            'faultType': 'HIGH_LATENCY',
            'severity': 'high',
            'detectedAt': timezone.now().isoformat(),
            'status': 'active',
            'description': 'Latency threshold exceeded',
        }, format='json')
        self.assertEqual(response.status_code, 405)
        self.assertFalse(FaultEvent.objects.exists())

        record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=timezone.now(),
            reachable=True,
            latency_ms=650.0,
            packet_loss_percent=0.0,
        )
        faults = evaluate_monitoring_record(record)
        self.assertEqual(len(faults), 1)
        self.assertEqual(faults[0].fault_type, FaultEvent.FaultType.HIGH_LATENCY)
        self.assertTrue(Notification.objects.filter(fault=faults[0]).exists())

    def test_fault_can_be_acknowledged_and_resolved(self):
        fault = FaultEvent.objects.create(
            device=self.device,
            fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
            severity=FaultEvent.Severity.CRITICAL,
            detected_at=timezone.now(),
        )
        response = self.client.post(f'/api/faults/{fault.id}/acknowledge/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'acknowledged')
        response = self.client.post(f'/api/faults/{fault.id}/resolve/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'resolved')
        self.assertIsNotNone(response.data['resolvedAt'])

    def test_notification_can_be_marked_read(self):
        fault = FaultEvent.objects.create(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
            severity=FaultEvent.Severity.HIGH,
            detected_at=timezone.now(),
        )
        notification = Notification.objects.get(fault=fault)
        response = self.client.post(f'/api/notifications/{notification.id}/read/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'read')

    def test_dashboard_requires_authentication(self):
        self.client.credentials()
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 401)

    def test_auth_login_and_me(self):
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'admin123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'admin')

    def test_auth_login_accepts_admin_email(self):
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {
            'username': 'admin@example.com',
            'password': 'admin123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['username'], 'admin')

    def test_auth_rejects_invalid_credentials(self):
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'wrong-password',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('token', response.data)

    def test_auth_rejects_non_administrator_login(self):
        User.objects.create_user(username='operator', password='operator123')
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {
            'username': 'operator',
            'password': 'operator123',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('token', response.data)

    def test_auth_password_is_hashed(self):
        self.assertNotEqual(self.user.password, 'admin123')
        self.assertTrue(self.user.check_password('admin123'))

    def test_logout_invalidates_token(self):
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 204)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)

    def test_authenticated_non_admin_user_is_forbidden(self):
        operator = User.objects.create_user(username='operator', password='operator123')
        token = Token.objects.create(user=operator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 403)


class BackendFoundationTests(APITestCase):
    def test_health_check_is_public_and_reports_database(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'ok', 'database': 'ok'})

    def test_health_check_rejects_non_get_requests(self):
        response = self.client.post('/api/health/', {}, format='json')
        self.assertEqual(response.status_code, 405)


class MonitoringEngineTests(APITestCase):
    def setUp(self):
        self.device = Device.objects.create(
            name='Monitoring Router',
            ip_address='10.0.0.1',
            device_type=Device.DeviceType.ROUTER,
        )

    @patch('network.monitoring.services.subprocess.run')
    def test_ping_ipv4_parses_latency(self, mock_run):
        from .monitoring import ping_ipv4

        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '64 bytes from 10.0.0.1: time=4.32 ms'
        mock_run.return_value.stderr = ''
        result = ping_ipv4('10.0.0.1')
        self.assertTrue(result.reachable)
        self.assertEqual(result.latency_ms, 4.32)
        self.assertEqual(result.packet_loss_percent, 0.0)
        mock_run.assert_called_once()
        self.assertFalse(mock_run.call_args.kwargs.get('shell', False))

    @patch('network.monitoring.services.subprocess.run', side_effect=__import__('subprocess').TimeoutExpired(cmd=['ping'], timeout=2))
    def test_ping_ipv4_handles_timeout(self, mock_run):
        from .monitoring import ping_ipv4

        result = ping_ipv4('10.0.0.1')
        self.assertFalse(result.reachable)
        self.assertIsNone(result.latency_ms)
        self.assertEqual(result.packet_loss_percent, 100.0)
        self.assertIn('timed out', result.error)

    def test_ping_ipv4_rejects_invalid_address(self):
        from .monitoring import ping_ipv4

        with self.assertRaises(InvalidMonitoringConfiguration):
            ping_ipv4('not-an-ip')

    @patch('network.monitoring.services.ping_ipv4')
    def test_monitor_device_persists_result_and_status(self, mock_ping):
        mock_ping.return_value = PingResult(True, 2.75, 0.0)
        record = monitor_device(self.device)
        self.assertEqual(record.device_id, self.device.id)
        self.assertTrue(record.reachable)
        self.assertEqual(record.latency_ms, 2.75)
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.ONLINE)

    @patch('network.monitoring.services.ping_ipv4')
    def test_monitor_device_persists_network_failure_as_unreachable(self, mock_ping):
        mock_ping.return_value = PingResult(False, None, 100.0, 'Network error')
        record = monitor_device(self.device)
        self.assertFalse(record.reachable)
        self.assertEqual(record.packet_loss_percent, 100.0)
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.OFFLINE)
