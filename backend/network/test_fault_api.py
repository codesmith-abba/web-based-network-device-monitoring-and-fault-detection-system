from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Device, FaultEvent


class FaultManagementAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.device = Device.objects.create(
            name='Core Router',
            ip_address='10.0.0.1',
            device_type=Device.DeviceType.ROUTER,
        )
        now = timezone.now()
        self.active_fault = FaultEvent.objects.create(
            device=self.device,
            fault_type=FaultEvent.FaultType.HIGH_LATENCY,
            severity=FaultEvent.Severity.HIGH,
            detected_at=now - timedelta(hours=1),
            status=FaultEvent.Status.ACTIVE,
            description='Latency exceeded threshold.',
        )
        self.resolved_fault = FaultEvent.objects.create(
            device=self.device,
            fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
            severity=FaultEvent.Severity.CRITICAL,
            detected_at=now - timedelta(days=1),
            status=FaultEvent.Status.RESOLVED,
            resolved_at=now - timedelta(hours=20),
            description='Device was unreachable.',
        )
        self.client.force_authenticate(self.user)

    def test_fault_list_is_protected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/faults/')
        self.assertEqual(response.status_code, 401)

    def test_fault_list_returns_frontend_contract(self):
        response = self.client.get('/api/faults/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        item = response.data['results'][0]
        self.assertIn('deviceId', item)
        self.assertIn('deviceName', item)
        self.assertIn('faultType', item)
        self.assertIn('severity', item)
        self.assertIn('detectedAt', item)
        self.assertIn('status', item)
        self.assertIn('resolvedAt', item)

    def test_active_fault_endpoint_excludes_resolved(self):
        response = self.client.get('/api/faults/active/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.active_fault.id))

    def test_fault_filters(self):
        response = self.client.get('/api/faults/', {'severity': 'high', 'type': 'HIGH_LATENCY'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.active_fault.id))

        response = self.client.get('/api/faults/', {'status': 'resolved', 'deviceId': str(self.device.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.resolved_fault.id))

    def test_fault_date_filters(self):
        start = (timezone.now() - timedelta(hours=2)).isoformat()
        response = self.client.get('/api/faults/', {'from': start})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.active_fault.id))

    def test_fault_detail(self):
        response = self.client.get(f'/api/faults/{self.active_fault.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deviceId'], str(self.device.id))
        self.assertEqual(response.data['deviceName'], self.device.name)

    def test_acknowledge_fault(self):
        response = self.client.post(f'/api/faults/{self.active_fault.id}/acknowledge/')
        self.assertEqual(response.status_code, 200)
        self.active_fault.refresh_from_db()
        self.assertEqual(self.active_fault.status, FaultEvent.Status.ACKNOWLEDGED)

    def test_resolve_fault(self):
        response = self.client.post(f'/api/faults/{self.active_fault.id}/resolve/')
        self.assertEqual(response.status_code, 200)
        self.active_fault.refresh_from_db()
        self.assertEqual(self.active_fault.status, FaultEvent.Status.RESOLVED)
        self.assertIsNotNone(self.active_fault.resolved_at)

    def test_status_endpoint_validates_transition(self):
        response = self.client.patch(
            f'/api/faults/{self.active_fault.id}/status/',
            {'status': 'acknowledged'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.active_fault.refresh_from_db()
        self.assertEqual(self.active_fault.status, FaultEvent.Status.ACKNOWLEDGED)

        response = self.client.patch(
            f'/api/faults/{self.active_fault.id}/status/',
            {'status': 'invalid'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_resolved_fault_cannot_be_reactivated(self):
        response = self.client.patch(
            f'/api/faults/{self.resolved_fault.id}/status/',
            {'status': 'active'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_fault_history_supports_same_filters(self):
        response = self.client.get('/api/fault-history/', {'status': 'resolved', 'type': 'DEVICE_UNREACHABLE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['faults']), 1)
        self.assertEqual(response.data['faults'][0]['id'], str(self.resolved_fault.id))
