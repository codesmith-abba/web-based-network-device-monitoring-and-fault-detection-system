from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Device, FaultEvent, MonitoringConfiguration, MonitoringRecord, Notification


User = get_user_model()


class NetworkApiTests(APITestCase):
    def setUp(self):
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

    def test_fault_creation_generates_notification(self):
        response = self.client.post('/api/faults/', {
            'device': str(self.device.id),
            'faultType': 'HIGH_LATENCY',
            'severity': 'high',
            'detectedAt': timezone.now().isoformat(),
            'status': 'active',
            'description': 'Latency threshold exceeded',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        fault = FaultEvent.objects.get(id=response.data['id'])
        self.assertTrue(Notification.objects.filter(fault=fault).exists())

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
