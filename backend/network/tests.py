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
