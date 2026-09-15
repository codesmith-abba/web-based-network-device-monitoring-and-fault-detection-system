from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Device, MonitoringConfiguration, SNMPMetric
from .snmp import SNMPMetricResult, collect_snmp_metrics


User = get_user_model()


class SNMPMonitoringTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='admin', password='admin123', is_staff=True)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.device = Device.objects.create(
            name='SNMP Router', ip_address='10.0.0.10', device_type=Device.DeviceType.ROUTER
        )
        self.configuration = MonitoringConfiguration.objects.get(device=self.device)
        self.configuration.snmp_enabled = True
        self.configuration.snmp_version = '2c'
        self.configuration.snmp_community = 'public'
        self.configuration.available_metrics = ['sysName', 'sysUpTime']
        self.configuration.save()

    @patch('network.snmp.services._get_metric')
    def test_collects_and_persists_supported_metrics(self, mock_get_metric):
        mock_get_metric.side_effect = lambda address, port, community, version, timeout, metric: {
            'sysName': SNMPMetricResult('sysName', '1.3.6.1.2.1.1.5.0', 'edge-router', 'OctetString'),
            'sysUpTime': SNMPMetricResult('sysUpTime', '1.3.6.1.2.1.1.3.0', '12345', 'TimeTicks'),
        }[metric]
        result = collect_snmp_metrics(self.device)
        self.assertEqual(result.status, 'success')
        self.assertEqual(len(result.metrics), 2)
        self.assertEqual(SNMPMetric.objects.filter(device=self.device).count(), 2)

    @patch('network.snmp.services._get_metric')
    def test_limited_metrics_are_supported_without_failing_other_metrics(self, mock_get_metric):
        def fake_get_metric(address, port, community, version, timeout, metric):
            if metric == 'sysUpTime':
                raise RuntimeError('No Such Object')
            return SNMPMetricResult('sysName', '1.3.6.1.2.1.1.5.0', 'edge-router', 'OctetString')

        mock_get_metric.side_effect = fake_get_metric
        result = collect_snmp_metrics(self.device)
        self.assertEqual(result.status, 'partial')
        self.assertEqual(len(result.metrics), 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(SNMPMetric.objects.filter(device=self.device).count(), 1)

    def test_disabled_snmp_does_not_fail_the_application(self):
        self.configuration.snmp_enabled = False
        self.configuration.save(update_fields=['snmp_enabled'])
        result = collect_snmp_metrics(self.device)
        self.assertEqual(result.status, 'disabled')
        self.assertEqual(result.metrics, ())

    def test_missing_credentials_are_reported_as_configuration_error(self):
        self.configuration.snmp_community = ''
        self.configuration.save(update_fields=['snmp_community'])
        result = collect_snmp_metrics(self.device)
        self.assertEqual(result.status, 'configuration_error')
        self.assertIn('community', result.errors[0])

    @patch('network.snmp.services._get_metric', side_effect=RuntimeError('No SNMP response received before timeout'))
    def test_agent_or_credential_failure_is_isolated(self, mock_get_metric):
        result = collect_snmp_metrics(self.device)
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(result.metrics), 0)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(SNMPMetric.objects.filter(device=self.device).count(), 0)

    def test_snmp_configuration_and_results_are_exposed_by_api(self):
        response = self.client.get(f'/api/devices/{self.device.id}/snmp/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['configuration']['snmpVersion'], '2c')
        self.assertNotIn('snmpCommunity', response.data['configuration'])
        self.assertIn('sysName', response.data['supportedMetrics'])

        SNMPMetric.objects.create(
            device=self.device,
            timestamp=timezone.now(),
            metric='sysName',
            oid='1.3.6.1.2.1.1.5.0',
            value='edge-router',
            value_type='OctetString',
        )
        response = self.client.get(f'/api/devices/{self.device.id}/monitoring-snapshot/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['snmpMetrics'][0]['metricName'], 'sysName')

    def test_snmp_configuration_can_be_updated(self):
        response = self.client.patch(
            f'/api/devices/{self.device.id}/snmp/',
            {
                'snmpEnabled': True,
                'snmpVersion': '1',
                'snmpCommunity': 'private',
                'snmpPort': 161,
                'snmpTimeoutSeconds': 3,
                'availableMetrics': ['sysDescr'],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.configuration.refresh_from_db()
        self.assertEqual(self.configuration.snmp_version, '1')
        self.assertEqual(self.configuration.snmp_community, 'private')
        self.assertEqual(self.configuration.available_metrics, ['sysDescr'])

    @patch('network.snmp.services._get_metric')
    def test_snmp_poll_endpoint_returns_mocked_metrics(self, mock_get_metric):
        mock_get_metric.return_value = SNMPMetricResult(
            'sysName', '1.3.6.1.2.1.1.5.0', 'edge-router', 'OctetString'
        )
        response = self.client.post(f'/api/devices/{self.device.id}/snmp/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['metrics'][0]['metricName'], 'sysName')
        self.assertEqual(SNMPMetric.objects.filter(device=self.device).count(), 2)

    def test_snmp_endpoint_requires_administrator(self):
        operator = User.objects.create_user(username='operator', password='operator123')
        token = Token.objects.create(user=operator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.post(f'/api/devices/{self.device.id}/snmp/', {}, format='json')
        self.assertEqual(response.status_code, 403)
