from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from .models import Device, MonitoringConfiguration, MonitoringRecord
from .monitoring import PingResult
from .snmp import SNMPResult
from .tasks import dispatch_due_monitoring_tasks, monitor_device_task


class FakeRedisLock:
    def __init__(self, acquired=True):
        self.acquired = acquired
        self.released = False

    def acquire(self):
        return self.acquired

    def release(self):
        self.released = True


class AutomatedMonitoringTaskTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(
            name='Automated Router',
            ip_address='192.168.10.10',
            device_type=Device.DeviceType.ROUTER,
        )
        self.configuration = MonitoringConfiguration.objects.get(device=self.device)

    @patch('network.tasks._redis_client')
    @patch('network.tasks.collect_snmp_metrics')
    @patch('network.tasks.monitor_device')
    def test_monitor_device_task_runs_icmp_and_snmp(self, mock_monitor, mock_snmp, mock_redis):
        lock = FakeRedisLock()
        mock_redis.return_value.lock.return_value = lock
        record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=timezone.now(),
            reachable=True,
            latency_ms=12.0,
            packet_loss_percent=0.0,
        )
        mock_monitor.return_value = record
        mock_snmp.return_value = SNMPResult('success', (), ())
        self.configuration.snmp_enabled = True
        self.configuration.snmp_community = 'public'
        self.configuration.snmp_version = '2c'
        self.configuration.save()

        result = monitor_device_task.run(str(self.device.id))

        mock_monitor.assert_called_once_with(self.device)
        mock_snmp.assert_called_once_with(self.device)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['monitoring_record_id'], str(record.id))
        self.assertTrue(lock.released)

    @patch('network.tasks._redis_client')
    def test_monitor_device_task_skips_overlapping_run(self, mock_redis):
        lock = FakeRedisLock(acquired=False)
        mock_redis.return_value.lock.return_value = lock

        with patch('network.tasks.monitor_device') as mock_monitor:
            result = monitor_device_task.run(str(self.device.id))

        mock_monitor.assert_not_called()
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'already_running')

    @patch('network.tasks._redis_client')
    def test_monitor_device_task_skips_disabled_device(self, mock_redis):
        lock = FakeRedisLock()
        mock_redis.return_value.lock.return_value = lock
        self.device.monitoring_enabled = False
        self.device.save(update_fields=['monitoring_enabled'])

        with patch('network.tasks.monitor_device') as mock_monitor:
            result = monitor_device_task.run(str(self.device.id))

        mock_monitor.assert_not_called()
        self.assertEqual(result['reason'], 'monitoring_disabled')

    @patch('network.tasks._redis_client')
    @patch('network.tasks.monitor_device')
    def test_monitor_device_task_survives_monitoring_failure(self, mock_monitor, mock_redis):
        lock = FakeRedisLock()
        mock_redis.return_value.lock.return_value = lock
        mock_monitor.side_effect = RuntimeError('ping failed')

        result = monitor_device_task.run(str(self.device.id))

        self.assertEqual(result['status'], 'partial')
        self.assertIn('icmp_error', result)
        self.assertTrue(lock.released)

    @patch('network.tasks.monitor_device_task.delay')
    def test_dispatches_only_due_devices(self, mock_delay):
        now = timezone.now()
        MonitoringRecord.objects.create(
            device=self.device,
            timestamp=now - timedelta(seconds=self.configuration.interval_seconds - 1),
            reachable=True,
            latency_ms=5,
            packet_loss_percent=0,
        )
        other = Device.objects.create(
            name='Due Switch',
            ip_address='192.168.10.11',
            device_type=Device.DeviceType.SWITCH,
        )
        other_config = MonitoringConfiguration.objects.get(device=other)
        other_config.interval_seconds = 30
        other_config.save(update_fields=['interval_seconds'])

        result = dispatch_due_monitoring_tasks.run()

        mock_delay.assert_called_once_with(str(other.id))
        self.assertEqual(result['dispatched'], 1)

    @patch('network.tasks._redis_client')
    @patch('network.tasks.collect_snmp_metrics')
    @patch('network.tasks.monitor_device')
    def test_snmp_failure_does_not_lose_icmp_result(self, mock_monitor, mock_snmp, mock_redis):
        lock = FakeRedisLock()
        mock_redis.return_value.lock.return_value = lock
        record = MonitoringRecord.objects.create(
            device=self.device,
            timestamp=timezone.now(),
            reachable=True,
            latency_ms=7,
            packet_loss_percent=0,
        )
        mock_monitor.return_value = record
        mock_snmp.side_effect = RuntimeError('SNMP timeout')
        self.configuration.snmp_enabled = True
        self.configuration.snmp_community = 'public'
        self.configuration.snmp_version = '2c'
        self.configuration.save()

        result = monitor_device_task.run(str(self.device.id))

        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['reachable'], True)
        self.assertEqual(result['snmp']['status'], 'error')
