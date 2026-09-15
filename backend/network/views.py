from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .alerts.services import create_fault_notification, mark_notification_read
from .faults.services import acknowledge_fault, resolve_fault
from .models import Device, FaultEvent, MonitoringRecord, Notification
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
from .snmp.services import collect_snmp_metrics


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.get_username(),
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'isStaff': user.is_staff,
            },
        })


class LogoutView(APIView):
    def post(self, request):
        if request.auth is not None:
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.get_username(),
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'isStaff': user.is_staff,
        })


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related('monitoring_configuration').all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_value = self.request.query_params.get('status')
        device_type = self.request.query_params.get('type')
        monitoring = self.request.query_params.get('monitoring')
        search = self.request.query_params.get('search')
        if status_value:
            queryset = queryset.filter(status=status_value)
        if device_type:
            queryset = queryset.filter(device_type=device_type)
        if monitoring is not None:
            queryset = queryset.filter(monitoring_enabled=monitoring.lower() in {'true', '1', 'yes'})
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    @action(detail=True, methods=['get', 'patch'], url_path='monitoring')
    def monitoring(self, request, pk=None):
        """Read or update only the device monitoring enabled state."""
        device = self.get_object()
        if request.method == 'PATCH':
            serializer = DeviceSerializer(
                device,
                data={'monitoring': request.data.get('monitoring')},
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            device.refresh_from_db()
        return Response(DeviceSerializer(device).data)

    @action(detail=True, methods=['get', 'patch'], url_path='monitoring-config')
    def monitoring_config(self, request, pk=None):
        device = self.get_object()
        config = device.monitoring_configuration
        if request.method == 'PATCH':
            serializer = MonitoringConfigurationSerializer(config, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(MonitoringConfigurationSerializer(config).data)

    @action(detail=True, methods=['post'], url_path='monitor')
    def monitor(self, request, pk=None):
        """Run one immediate ICMP monitoring check and persist the result."""
        device = self.get_object()
        try:
            record = monitor_device(device)
        except InvalidMonitoringConfiguration as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MonitoringRecordSerializer(record).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='monitoring-snapshot')
    def monitoring_snapshot(self, request, pk=None):
        device = self.get_object()
        configuration = device.monitoring_configuration
        latest = device.monitoring_records.first()
        history = device.monitoring_records.all()[:50]
        snmp_metrics = device.snmp_metrics.order_by('-timestamp')

        latest_by_metric = {}
        for metric in snmp_metrics:
            if metric.metric not in latest_by_metric:
                latest_by_metric[metric.metric] = metric

        configured_metrics = configuration.available_metrics or []
        metric_names = list(dict.fromkeys([*configured_metrics, *latest_by_metric.keys()]))
        snapshot_metrics = []
        for metric_name in metric_names:
            metric = latest_by_metric.get(metric_name)
            snapshot_metrics.append({
                'name': metric_name,
                'value': metric.value if metric else None,
                'available': metric is not None,
            })

        return Response({
            'device': DeviceSerializer(device).data,
            'latest': MonitoringRecordSerializer(latest).data if latest else None,
            'history': MonitoringRecordSerializer(history, many=True).data,
            'snmpMetrics': snapshot_metrics,
            'configuration': MonitoringConfigurationSerializer(configuration).data,
        })

    @action(detail=True, methods=['get'], url_path='monitoring-summary')
    def monitoring_summary(self, request, pk=None):
        device = self.get_object()
        queryset = device.monitoring_records.all()
        now = timezone.now()
        window = request.query_params.get('hours')
        try:
            hours = max(1, min(168, int(window))) if window else 24
        except (TypeError, ValueError):
            hours = 24
        queryset = queryset.filter(timestamp__gte=now - timedelta(hours=hours))
        total = queryset.count()
        reachable = queryset.filter(reachable=True).count()
        return Response({
            'deviceId': str(device.id),
            'hours': hours,
            'records': total,
            'availability': (reachable / total * 100) if total else None,
            'averageLatencyMs': queryset.exclude(latency_ms__isnull=True).aggregate(models.Avg('latency_ms')).get('latency_ms__avg'),
            'averagePacketLossPercent': queryset.exclude(packet_loss_percent__isnull=True).aggregate(models.Avg('packet_loss_percent')).get('packet_loss_percent__avg'),
        })

    @action(detail=True, methods=['post'], url_path='snmp/poll')
    def snmp_poll(self, request, pk=None):
        device = self.get_object()
        result = collect_snmp_metrics(device)
        return Response({
            'status': result.status,
            'metrics': SNMPMetricSerializer(
                device.snmp_metrics.filter(timestamp__gte=timezone.now() - timedelta(seconds=5)),
                many=True,
            ).data,
            'errors': list(result.errors),
        }, status=status.HTTP_200_OK if result.status in {'success', 'partial'} else status.HTTP_400_BAD_REQUEST)


class MonitoringRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonitoringRecord.objects.select_related('device').all()
    serializer_class = MonitoringRecordSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        device_id = self.request.query_params.get('deviceId')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset


class FaultViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = FaultEvent.objects.select_related('device').all()
    serializer_class = FaultSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {
            'deviceId': 'device_id',
            'severity': 'severity',
            'type': 'fault_type',
            'faultType': 'fault_type',
            'status': 'status',
        }
        for key, field in filters.items():
            value = self.request.query_params.get(key)
            if value:
                queryset = queryset.filter(**{field: value})
        start = self.request.query_params.get('from')
        end = self.request.query_params.get('to')
        if start:
            queryset = queryset.filter(detected_at__gte=start)
        if end:
            queryset = queryset.filter(detected_at__lte=end)
        return queryset

    def perform_create(self, serializer):
        fault = serializer.save()
        create_fault_notification(fault)

    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.get_queryset().filter(status__in=[FaultEvent.Status.ACTIVE, FaultEvent.Status.ACKNOWLEDGED])
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        fault = acknowledge_fault(self.get_object())
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
            return Response({'detail': 'Invalid fault status.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == FaultEvent.Status.ACKNOWLEDGED:
            try:
                fault = acknowledge_fault(fault)
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        elif new_status == FaultEvent.Status.RESOLVED:
            fault = resolve_fault(fault)
        else:
            if fault.status == FaultEvent.Status.RESOLVED:
                return Response({'detail': 'Resolved faults cannot be reactivated through the API.'}, status=status.HTTP_400_BAD_REQUEST)
            fault.status = FaultEvent.Status.ACTIVE
            fault.save(update_fields=['status'])
        return Response(self.get_serializer(fault).data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.select_related('fault__device').all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_value = self.request.query_params.get('status')
        if status_value:
            queryset = queryset.filter(status=status_value)
        device_id = self.request.query_params.get('deviceId')
        if device_id:
            queryset = queryset.filter(fault__device_id=device_id)
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(fault__severity=severity)
        return queryset

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
            availability = None if latest is None else (100 if latest.reachable else 0)
            device_health.append({'id': str(device.id), 'name': device.name, 'address': device.ip_address, 'type': device.device_type, 'status': device.status, 'availability': availability, 'latencyMs': latest.latency_ms if latest else None, 'packetLossPercent': latest.packet_loss_percent if latest else None})
        faults = active_faults[:10]
        return Response({'summary': {'totalDevices': devices.count(), 'onlineDevices': devices.filter(status=Device.Status.ONLINE).count(), 'offlineDevices': devices.filter(status=Device.Status.OFFLINE).count(), 'activeFaults': active_faults.count()}, 'deviceHealth': device_health, 'activeFaults': [{'id': str(fault.id), 'deviceName': fault.device.name, 'title': fault.get_fault_type_display(), 'severity': fault.severity, 'detectedAt': fault.detected_at, 'description': fault.description or None} for fault in faults]})


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