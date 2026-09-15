from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import FaultEvent, Notification
from .monitoring import PingResult


User = get_user_model()


class FullSystemIntegrationTests(APITestCase):
    """Verify the documented administrator-to-monitoring workflow at the API boundary."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='integration-admin',
            email='integration@example.com',
            password='integration123',
            is_staff=True,
        )

    def authenticate(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'integration-admin', 'password': 'integration123'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")

    def test_documented_monitoring_fault_history_notification_workflow(self):
        # Administrator login.
        self.authenticate()

        # Register a monitored device.
        response = self.client.post(
            '/api/devices/',
            {
                'name': 'Integration Router',
                'ipAddress': '192.0.2.10',
                'type': 'router',
                'monitoring': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        device_id = response.data['id']

        # Configure the background polling interval through the real API.
        response = self.client.patch(
            f'/api/devices/{device_id}/monitoring-config/',
            {'intervalSeconds': 5},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['intervalSeconds'], 5)
        self.assertTrue(response.data['enabled'])

        # Run a controlled high-latency ICMP check through the real monitor endpoint.
        with patch('network.monitoring.services.ping_ipv4') as ping:
            ping.return_value = PingResult(True, 650.0, 0.0)
            response = self.client.post(f'/api/devices/{device_id}/monitor/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['reachable'])
        self.assertEqual(response.data['latencyMs'], 650.0)

        # Monitoring result -> fault evaluation -> FaultEvent -> Notification.
        fault = FaultEvent.objects.get(
            device_id=device_id,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
        )
        self.assertEqual(fault.status, FaultEvent.Status.ACTIVE)
        self.assertTrue(Notification.objects.filter(fault=fault).exists())

        # Dashboard reflects the monitored device and active fault.
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['totalDevices'], 1)
        self.assertEqual(response.data['summary']['activeFaults'], 1)
        self.assertEqual(response.data['deviceHealth'][0]['latencyMs'], 650.0)

        # Monitoring and fault history contain the generated records.
        response = self.client.get(f'/api/monitoring-history/?deviceId={device_id}')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['meta']['total'], 1)

        response = self.client.get(f'/api/fault-history/?deviceId={device_id}')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['meta']['total'], 1)

        # Notification is visible and can be marked as read.
        notification = Notification.objects.get(fault=fault)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], str(notification.id))

        response = self.client.post(f'/api/notifications/{notification.id}/read/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], Notification.Status.READ)

        # Fault acknowledgement and explicit resolution work through the API.
        response = self.client.post(f'/api/faults/{fault.id}/acknowledge/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], FaultEvent.Status.ACKNOWLEDGED)

        response = self.client.post(f'/api/faults/{fault.id}/resolve/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], FaultEvent.Status.RESOLVED)

        # A healthy subsequent check exercises automatic recovery evaluation.
        with patch('network.monitoring.services.ping_ipv4') as ping:
            ping.return_value = PingResult(True, 20.0, 0.0)
            response = self.client.post(f'/api/devices/{device_id}/monitor/', {}, format='json')
        self.assertEqual(response.status_code, 200)

        # The device monitoring snapshot exposes the final persisted state.
        response = self.client.get(f'/api/devices/{device_id}/monitoring-snapshot/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['device']['id'], device_id)
        self.assertEqual(response.data['latest']['latencyMs'], 20.0)
        self.assertGreaterEqual(len(response.data['history']), 2)
