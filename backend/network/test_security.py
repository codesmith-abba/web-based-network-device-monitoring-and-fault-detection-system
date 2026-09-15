from datetime import timedelta
from unittest.mock import patch

import redis
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Device, FaultEvent
from .tasks import monitor_device_task


User = get_user_model()


class AuthenticationSecurityTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='security-admin',
            email='security-admin@example.com',
            password='StrongPassword123!',
            is_staff=True,
        )
        self.non_staff = User.objects.create_user(
            username='regular-user',
            email='regular@example.com',
            password='StrongPassword123!',
            is_staff=False,
        )

    def test_anonymous_protected_api_is_rejected(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 401)

    def test_non_staff_user_cannot_access_admin_api(self):
        self.client.force_authenticate(self.non_staff)
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_non_staff_user_cannot_login(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'regular-user', 'password': 'StrongPassword123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('token', response.data)

    def test_successful_login_rotates_previous_token(self):
        first = self.client.post(
            '/api/auth/login/',
            {'username': 'security-admin', 'password': 'StrongPassword123!'},
            format='json',
        )
        second = self.client.post(
            '/api/auth/login/',
            {'username': 'security-admin', 'password': 'StrongPassword123!'},
            format='json',
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.data['token'], second.data['token'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {first.data['token']}")
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {second.data['token']}")
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

    def test_login_is_rate_limited(self):
        responses = [
            self.client.post(
                '/api/auth/login/',
                {'username': 'security-admin', 'password': 'wrong-password'},
                format='json',
            )
            for _ in range(6)
        ]
        self.assertTrue(all(response.status_code == 400 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)


class InputAndAuthorizationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='input-admin',
            password='StrongPassword123!',
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def create_device(self):
        response = self.client.post(
            '/api/devices/',
            {
                'name': 'Security Router',
                'ipAddress': '192.0.2.50',
                'type': 'router',
                'monitoring': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        return response.data['id']

    def test_invalid_device_input_is_rejected(self):
        response = self.client.post(
            '/api/devices/',
            {
                'name': ' ',
                'ipAddress': 'not-an-ip',
                'type': 'invalid',
                'monitoring': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_monitoring_configuration_bounds_are_enforced(self):
        device_id = self.create_device()
        response = self.client.patch(
            f'/api/devices/{device_id}/monitoring-config/',
            {'intervalSeconds': 1, 'snmpPort': 70000, 'snmpTimeoutSeconds': 0},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_snmp_community_is_never_returned_by_configuration_api(self):
        device_id = self.create_device()
        response = self.client.patch(
            f'/api/devices/{device_id}/monitoring-config/',
            {
                'snmpEnabled': True,
                'snmpVersion': '2c',
                'snmpCommunity': 'private-community',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('snmpCommunity', response.data)

    def test_faults_cannot_be_created_directly_through_api(self):
        device_id = self.create_device()
        response = self.client.post(
            '/api/faults/',
            {
                'device': device_id,
                'faultType': FaultEvent.FaultType.HIGH_LATENCY,
                'severity': FaultEvent.Severity.HIGH,
                'detectedAt': timezone.now().isoformat(),
                'status': FaultEvent.Status.ACTIVE,
                'description': 'Client-created fault',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(FaultEvent.objects.count(), 0)


class DatabaseAndConfigurationSecurityTests(TestCase):
    def test_active_fault_database_constraint_prevents_duplicate_fault_type(self):
        device = Device.objects.create(
            name='Integrity Router',
            ip_address='192.0.2.60',
            device_type=Device.DeviceType.ROUTER,
        )
        FaultEvent.objects.create(
            device=device,
            fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
            severity=FaultEvent.Severity.CRITICAL,
            detected_at=timezone.now(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FaultEvent.objects.create(
                    device=device,
                    fault_type=FaultEvent.FaultType.DEVICE_UNREACHABLE,
                    severity=FaultEvent.Severity.CRITICAL,
                    detected_at=timezone.now() + timedelta(seconds=1),
                )

    @override_settings(DEBUG=False)
    def test_production_debug_is_disabled(self):
        self.assertFalse(settings.DEBUG)
        self.assertNotIn('development-only', settings.SECRET_KEY)
        self.assertNotIn('change-me', settings.SECRET_KEY)

    def test_security_headers_are_enabled(self):
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(settings.X_FRAME_OPTIONS, 'DENY')

    def test_cors_is_explicit_not_wildcard(self):
        self.assertNotIn('*', settings.CORS_ALLOWED_ORIGINS)


class MonitoringDependencyFailureTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(
            name='Redis Failure Router',
            ip_address='192.0.2.70',
            device_type=Device.DeviceType.ROUTER,
        )

    def test_redis_lock_failure_returns_dependency_error(self):
        with patch('network.tasks._redis_client', side_effect=redis.ConnectionError('simulated Redis outage')):
            result = monitor_device_task.run(str(self.device.id))

        self.assertEqual(result['status'], 'dependency_error')
        self.assertEqual(result['reason'], 'redis_unavailable')
