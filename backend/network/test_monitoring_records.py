from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Device, MonitoringRecord
from .monitoring import PingResult, ping_ipv4


User = get_user_model()


class MonitoringRecordTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='monitor-admin',
            password='admin123',
            is_staff=True,
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.device = Device.objects.create(
            name='History Router',
            ip_address='10.0.0.20',
            device_type=Device.DeviceType.ROUTER,
        )

    def test_monitoring_record_persists_each_result_without_overwriting_history(self):
        first_timestamp = timezone.now() - timedelta(minutes=2)
        second_timestamp = timezone.now()

        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=first_timestamp,
            reachable=True,
            latency_ms=10.0,
            packet_loss_percent=0.0,
        )
        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=second_timestamp,
            reachable=False,
            latency_ms=None,
            packet_loss_percent=100.0,
        )

        self.assertEqual(MonitoringRecord.objects.filter(device=self.device).count(), 2)
        self.assertEqual(MonitoringRecord.objects.filter(device=self.device).order_by('timestamp').first().latency_ms, 10.0)
        self.assertEqual(MonitoringRecord.objects.filter(device=self.device).first().packet_loss_percent, 100.0)

    @patch('network.monitoring.ping_ipv4')
    def test_monitoring_records_store_packet_loss_and_update_status(self, mock_ping):
        mock_ping.return_value = PingResult(False, None, 75.0, 'Partial packet loss.')

        response = self.client.post(f'/api/devices/{self.device.id}/monitor/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['packetLossPercent'], 75.0)
        self.device.refresh_from_db()
        self.assertEqual(self.device.status, Device.Status.OFFLINE)

    @patch('network.monitoring.subprocess.run')
    def test_ping_ipv4_parses_supported_packet_loss_output(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '64 bytes from 10.0.0.20: time=8.10 ms\n'
            '4 packets transmitted, 3 received, 25% packet loss\n'
        )
        mock_run.return_value.stderr = ''

        result = ping_ipv4('10.0.0.20')

        self.assertTrue(result.reachable)
        self.assertEqual(result.latency_ms, 8.10)
        self.assertEqual(result.packet_loss_percent, 25.0)

    def test_monitoring_summary_reports_latest_and_aggregates(self):
        now = timezone.now()
        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=now - timedelta(minutes=2),
            reachable=True,
            latency_ms=10.0,
            packet_loss_percent=0.0,
        )
        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=now - timedelta(minutes=1),
            reachable=True,
            latency_ms=20.0,
            packet_loss_percent=10.0,
        )
        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=now,
            reachable=False,
            latency_ms=None,
            packet_loss_percent=100.0,
        )

        response = self.client.get(f'/api/devices/{self.device.id}/monitoring-summary/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['totalRecords'], 3)
        self.assertEqual(response.data['reachableRecords'], 2)
        self.assertEqual(response.data['unreachableRecords'], 1)
        self.assertEqual(response.data['availabilityPercent'], 66.67)
        self.assertEqual(response.data['averageLatencyMs'], 15.0)
        self.assertEqual(response.data['averagePacketLossPercent'], 36.667)
        self.assertEqual(response.data['latest']['packetLossPercent'], 100.0)

    def test_monitoring_history_supports_device_and_time_filters(self):
        now = timezone.now()
        old_record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=now - timedelta(hours=2),
            reachable=True,
            latency_ms=8.0,
            packet_loss_percent=0.0,
        )
        recent_record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=now - timedelta(minutes=5),
            reachable=True,
            latency_ms=12.0,
            packet_loss_percent=0.0,
        )

        response = self.client.get(
            '/api/monitoring-history/',
            {
                'deviceId': str(self.device.id),
                'from': (now - timedelta(minutes=10)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.data['records']]
        self.assertEqual(ids, [str(recent_record.id)])
        self.assertNotIn(str(old_record.id), ids)

    def test_monitoring_summary_is_empty_before_first_measurement(self):
        response = self.client.get(f'/api/devices/{self.device.id}/monitoring-summary/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['totalRecords'], 0)
        self.assertIsNone(response.data['availabilityPercent'])
        self.assertIsNone(response.data['averageLatencyMs'])
        self.assertIsNone(response.data['latest'])
