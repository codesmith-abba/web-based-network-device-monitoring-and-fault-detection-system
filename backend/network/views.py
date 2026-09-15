from django.db.models import Avg, Count, Max
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .alerts.services import mark_notification_read
from .devices.services import ensure_monitoring_configuration
from .faults.services import acknowledge_fault, resolve_fault
from .models import Device, FaultEvent, MonitoringConfiguration, MonitoringRecord, Notification, SNMPMetric
from .monitoring import InvalidMonitoringConfiguration, monitor_device
from .serializers import (
    DeviceSerializer,
    FaultSerializer,
    HistoricalMonitoringRecordSerializer,
    LoginSerializer,
    MonitoringConfigurationSerializer,
    MonitoringRecordSerializer,
    NotificationSerializer,
    SNMPMetricSerializer,
)
from .snmp import collect_snmp_metrics, get_supported_metrics


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related('monitoring_configuration').all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'patch', 'put', 'delete', 'head', 'options']

    @action(detail=True, methods=['patch'], url_path='monitoring')
    def monitoring(self, request, pk=None):
        device = self.get_object()
        serializer = self.get_serializer(device, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        ensure_monitoring_configuration(device)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='monitor')
    def monitor(self, request, pk=None):
        """Run one ICMP check and persist its monitoring result."""
        device = self.get_object()
        try:
            record = monitor_device(device)
        except InvalidMonitoringConfiguration as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MonitoringRecordSerializer(record).data)

    @action(detail=True, methods=['get'], url_path='monitoring-summary')
    def monitoring_summary(self, request, pk=None):
        """Return a compact health summary without modifying historical records."""
        device = self.get_object()
        queryset = MonitoringRecord.objects.filter(device=device)
        aggregates = queryset.aggregate(
            total=Count('id'),
            reachable=Count('id', filter=models.Q(reachable=True)),
            unreachable=Count('id', filter=models.Q(reachable=False)),
            average_latency=Avg('latency_ms'),
            average_packet_loss=Avg('packet_loss_percent'),
            last_checked=Max('timestamp'),
        )
        latest = queryset.first()
        total = aggregates['total'] or 0
        reachable = aggregates['reachable'] or 0
        availability = round((reachable / total) * 100, 2) if total else None

        return Response({
            'deviceId': str(device.id),
            'deviceName': device.name,
            'status': device.status,
            'monitoringEnabled': device.monitoring_enabled,
            'totalRecords': total,
            'reachableRecords': reachable,
            'unreachableRecords': aggregates['unreachable'] or 0,
            'availabilityPercent': availability,
            'averageLatencyMs': round(aggregates['average_latency'], 3) if aggregates['average_latency'] is not None else None,
            'averagePacketLossPercent': round(aggregates['average_packet_loss'], 3) if aggregates['average_packet_loss'] is not None else None,
            'lastCheckedAt': aggregates['last_checked'],
            'latest': MonitoringRecordSerializer(latest).data if latest else None,
        })

    @action(detail=True, methods=['get', 'patch', 'post'], url_path='snmp')
    def snmp(self, request, pk=None):
        """Configure, inspect, or poll SNMP without affecting ICMP monitoring."""
        device = self.get_object()
        configuration = ensure_monitoring_configuration(device)

        if request.method == 'GET':
            metrics = SNMPMetric.objects.filter(device=device)[:100]
            return Response({
                'configuration': MonitoringConfigurationSerializer(configuration).data,
                'supportedMetrics': get_supported_metrics(),
                'metrics': SNMPMetricSerializer(metrics, many=True).data,
            })

        if request.method == 'PATCH':
            serializer = MonitoringConfigurationSerializer(
                configuration,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            configuration = serializer.save()
            return Response(MonitoringConfigurationSerializer(configuration).data)

        result = collect_snmp_metrics(device)
        return Response({
            'status': result.status,
            'metrics': [
                {
                    'metricName': item.metric,
                    'oid': item.oid,
                    'value': item.value,
                    'valueType': item.value_type,
                }
                for item in result.metrics
            ],
            'errors': list(result.errors),
        })

    @action(detail=True, methods=['get'], url_path='monitoring-snapshot')
    def monitoring_snapshot(self, request, pk=None):
        device = self.get_object()
        configuration = ensure_monitoring_configuration(device)
        records = MonitoringRecord.objects.filter(device=device)[:50]
        latest = records[0] if records else None
        snmp_metrics = SNMPMetric.objects.filter(device=device)[:50]
        return Response({
            'device': DeviceSerializer(device).data,
            'latest': MonitoringRecordSerializer(latest).data if latest else None,
            'history': MonitoringRecordSerializer(records, many=True).data,
            'snmpMetrics': SNMPMetricSerializer(snmp_metrics, many=True).data,
            'configuration': MonitoringConfigurationSerializer(configuration).data,
        })


class MonitoringRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonitoringRecord.objects.select_related('device').all()
    serializer_class = MonitoringRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        device_id = self.request.query_params.get('deviceId')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset


class FaultViewSet(viewsets.ModelViewSet):
    queryset = FaultEvent.objects.select_related('device').all()
    serializer_class = FaultSerializer
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        fault = self.get_object()
        try:
            fault = acknowledge_fault(fault)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(fault).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        fault = resolve_fault(self.get_object())
        return Response(self.get_serializer(fault).data)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        fault = self.get_object()
        new_status = request.data.get('status')
        if new_status not in FaultEvent.Status.values:
            return Response({'status': 'Invalid fault status.'}, status=status.HTTP_400_BAD_REQUEST)
        fault.status = new_status
        if new_status == FaultEvent.Status.RESOLVED and fault.resolved_at is None:
            fault.resolved_at = timezone.now()
        if new_status != FaultEvent.Status.RESOLVED:
            fault.resolved_at = None
        fault.save(update_fields=['status', 'resolved_at'])
        return Response(self.get_serializer(fault).data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.select_related('fault__device').all()
    serializer_class = NotificationSerializer

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        notification = mark_notification_read(self.get_object())
        return Response(self.get_serializer(notification).data)


class DashboardView(APIView):
    def get(self, request):
        devices = Device.objects.all()
        active_faults = FaultEvent.objects.filter(status__in=[FaultEvent.Status.ACTIVE, FaultEvent.Status.ACKNOWLEDGED])
        device_health = []
        for device in devices:
            latest = device.monitoring_records.first()
            availability = None
            if latest is not None:
                availability = 100 if latest.reachable else 0
            device_health.append({
                'id': str(device.id),
                'name': device.name,
                'address': device.ip_address,
                'type': device.device_type,
                'status': device.status,
                'availability': availability,
                'latencyMs': latest.latency_ms if latest else None,
                'packetLossPercent': latest.packet_loss_percent if latest else None,
            })

        faults = active_faults[:10]
        return Response({
            'summary': {
                'totalDevices': devices.count(),
                'onlineDevices': devices.filter(status=Device.Status.ONLINE).count(),
                'offlineDevices': devices.filter(status=Device.Status.OFFLINE).count(),
                'activeFaults': active_faults.count(),
            },
            'deviceHealth': device_health,
            'activeFaults': [
                {
                    'id': str(fault.id),
                    'deviceName': fault.device.name,
                    'title': fault.get_fault_type_display(),
                    'severity': fault.severity,
                    'detectedAt': fault.detected_at,
                    'description': fault.description or None,
                }
                for fault in faults
            ],
        })


class MonitoringHistoryView(APIView):
    def get(self, request):
        queryset = MonitoringRecord.objects.select_related('device').all()
        device_id = request.query_params.get('deviceId')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        start = request.query_params.get('from')
        end = request.query_params.get('to')
        if start:
            queryset = queryset.filter(timestamp__gte=start)
        if end:
            queryset = queryset.filter(timestamp__lte=end)
        return Response({'records': HistoricalMonitoringRecordSerializer(queryset[:500], many=True).data})


class FaultHistoryView(APIView):
    def get(self, request):
        queryset = FaultEvent.objects.select_related('device').all()
        for key in ('deviceId', 'severity', 'status', 'faultType'):
            value = request.query_params.get(key)
            if value:
                field = {'deviceId': 'device_id', 'faultType': 'fault_type'}.get(key, key)
                queryset = queryset.filter(**{field: value})
        start = request.query_params.get('from')
        end = request.query_params.get('to')
        if start:
            queryset = queryset.filter(detected_at__gte=start)
        if end:
            queryset = queryset.filter(detected_at__lte=end)
        return Response({'faults': FaultSerializer(queryset[:500], many=True).data})


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.pk,
                'username': user.get_username(),
                'email': user.email,
            },
        })


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({'id': user.pk, 'username': user.get_username(), 'email': user.email})


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
