from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Device, FaultEvent, MonitoringRecord


User = get_user_model()


class HistoricalAnalyticsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='history-admin',
            password='admin123',
            is_staff=True,
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.device = Device.objects.create(
            name='History Router',
            ip_address='10.0.0.10',
            device_type=Device.DeviceType.ROUTER,
        )
        self.other_device = Device.objects.create(
            name='History Server',
            ip_address='10.0.0.20',
            device_type=Device.DeviceType.SERVER,
        )
        self.now = timezone.now().replace(second=0, microsecond=0)

    def create_record(self, device, minutes_ago, reachable=True, latency=10.0, loss=0.0):
        return MonitoringRecord.objects.create(
            device=device,
            timestamp=self.now - timedelta(minutes=minutes_ago),
            reachable=reachable,
            latency_ms=latency,
            packet_loss_percent=loss,
        )

    def test_monitoring_history_supports_device_and_date_filters(self):
        old = self.create_record(self.device, 120)
        recent = self.create_record(self.device, 10, latency=20.0)
        self.create_record(self.other_device, 10)

        response = self.client.get(
            '/api/monitoring-history/',
            {
                'deviceId': str(self.device.id),
                'from': (self.now - timedelta(minutes=30)).isoformat(),
                'to': self.now.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['records']), 1)
        self.assertEqual(response.data['records'][0]['id'], str(recent.id))
        self.assertNotEqual(response.data['records'][0]['id'], str(old.id))
        self.assertEqual(response.data['meta']['mode'], 'raw')

    def test_monitoring_history_aggregates_in_database(self):
        self.create_record(self.device, 2, latency=10.0, loss=0.0)
        self.create_record(self.device, 2, reachable=False, latency=None, loss=100.0)
        self.create_record(self.device, 62, latency=30.0, loss=0.0)

        response = self.client.get(
            '/api/monitoring-history/',
            {'deviceId': str(self.device.id), 'aggregation': 'hour'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['mode'], 'aggregated')
        self.assertEqual(response.data['meta']['aggregation'], 'hour')
        self.assertEqual(len(response.data['buckets']), 2)
        latest = response.data['buckets'][-1]
        self.assertEqual(latest['records'], 2)
        self.assertEqual(latest['reachableRecords'], 1)
        self.assertEqual(latest['availabilityPercent'], 50.0)
        self.assertEqual(latest['averageLatencyMs'], 10.0)
        self.assertEqual(latest['averagePacketLossPercent'], 50.0)

    def test_monitoring_history_rejects_invalid_range(self):
        response = self.client.get(
            '/api/monitoring-history/',
            {
                'from': self.now.isoformat(),
                'to': (self.now - timedelta(hours=1)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('earlier than or equal', response.data['detail'])

    def test_monitoring_history_requires_administrator(self):
        self.client.credentials()
        response = self.client.get('/api/monitoring-history/')
        self.assertEqual(response.status_code, 401)

    def create_fault(self, device, days_ago, fault_type, severity, status='active'):
        return FaultEvent.objects.create(
            device=device,
            fault_type=fault_type,
            severity=severity,
            detected_at=self.now - timedelta(days=days_ago),
            status=status,
            description='Historical fault',
        )

    def test_fault_history_supports_filters_and_date_ranges(self):
        recent = self.create_fault(
            self.device,
            0,
            FaultEvent.FaultType.HIGH_LATENCY,
            FaultEvent.Severity.HIGH,
        )
        self.create_fault(
            self.device,
            10,
            FaultEvent.FaultType.HIGH_PACKET_LOSS,
            FaultEvent.Severity.MEDIUM,
        )
        self.create_fault(
            self.other_device,
            0,
            FaultEvent.FaultType.DEVICE_UNREACHABLE,
            FaultEvent.Severity.CRITICAL,
        )

        response = self.client.get(
            '/api/fault-history/',
            {
                'deviceId': str(self.device.id),
                'severity': FaultEvent.Severity.HIGH,
                'from': (self.now - timedelta(days=1)).isoformat(),
                'to': (self.now + timedelta(minutes=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['faults']), 1)
        self.assertEqual(response.data['faults'][0]['id'], str(recent.id))

    def test_fault_history_aggregates_by_day(self):
        self.create_fault(
            self.device,
            0,
            FaultEvent.FaultType.HIGH_LATENCY,
            FaultEvent.Severity.HIGH,
        )
        self.create_fault(
            self.device,
            0,
            FaultEvent.FaultType.DEVICE_UNREACHABLE,
            FaultEvent.Severity.CRITICAL,
            status=FaultEvent.Status.RESOLVED,
        )

        response = self.client.get(
            '/api/fault-history/',
            {'deviceId': str(self.device.id), 'aggregation': 'day'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['buckets']), 1)
        bucket = response.data['buckets'][0]
        self.assertEqual(bucket['faults'], 2)
        self.assertEqual(bucket['status']['active'], 1)
        self.assertEqual(bucket['status']['resolved'], 1)
        self.assertEqual(bucket['severity']['critical'], 1)
        self.assertEqual(bucket['severity']['high'], 1)

    def test_fault_history_rejects_unsupported_aggregation(self):
        response = self.client.get('/api/fault-history/?aggregation=hour')
        self.assertEqual(response.status_code, 400)
        self.assertIn('currently supports', response.data['detail'])

    def test_history_limit_is_bounded(self):
        for minutes in range(3):
            self.create_record(self.device, minutes)

        response = self.client.get('/api/monitoring-history/?limit=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['records']), 2)
        self.assertEqual(response.data['meta']['limit'], 2)
