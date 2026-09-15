from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Device, FaultEvent, MonitoringRecord, Notification


User = get_user_model()


class NetworkApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='admin123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.device = Device.objects.create(
            name='Router 1',
            ip_address='192.168.1.1',
            type=Device.DeviceType.ROUTER,
            status=Device.Status.ONLINE,
        )

    def test_devices_list_uses_frontend_contract(self):
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], 'Router 1')
        self.assertEqual(response.data[0]['ipAddress'], '192.168.1.1')
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
        self.assertTrue(hasattr(created, 'monitoring_configuration'))

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
