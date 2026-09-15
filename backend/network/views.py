from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .models import Device, FaultEvent, MonitoringConfiguration, MonitoringRecord, Notification
from .serializers import (
    DeviceSerializer,
    FaultSerializer,
    HistoricalMonitoringRecordSerializer,
    LoginSerializer,
    MonitoringConfigurationSerializer,
    MonitoringRecordSerializer,
    NotificationSerializer,
)


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    @action(detail=True, methods=['patch'], url_path='monitoring')
    def monitoring(self, request, pk=None):
        device = self.get_object()
        serializer = self.get_serializer(device, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='monitoring-snapshot')
    def monitoring_snapshot(self, request, pk=None):
        device = self.get_object()
        configuration, _ = MonitoringConfiguration.objects.get_or_create(device=device)
        records = MonitoringRecord.objects.filter(device=device)[:50]
        latest = records[0] if records else None
        return Response({
            'device': DeviceSerializer(device).data,
            'latest': MonitoringRecordSerializer(latest).data if latest else None,
            'history': MonitoringRecordSerializer(records, many=True).data,
            'snmpMetrics': [],
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
        if fault.status == FaultEvent.Status.RESOLVED:
            return Response({'detail': 'Resolved faults cannot be acknowledged.'}, status=status.HTTP_400_BAD_REQUEST)
        fault.status = FaultEvent.Status.ACKNOWLEDGED
        fault.save(update_fields=['status'])
        return Response(self.get_serializer(fault).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        fault = self.get_object()
        fault.status = FaultEvent.Status.RESOLVED
        fault.resolved_at = timezone.now()
        fault.save(update_fields=['status', 'resolved_at'])
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
        notification = self.get_object()
        notification.status = Notification.Status.READ
        notification.save(update_fields=['status'])
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
                'type': device.type,
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
