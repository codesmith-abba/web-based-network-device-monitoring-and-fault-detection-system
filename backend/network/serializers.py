from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import Device, FaultEvent, MonitoringConfiguration, MonitoringRecord, Notification


User = get_user_model()


class DeviceSerializer(serializers.ModelSerializer):
    ipAddress = serializers.IPAddressField(source='ip_address')
    monitoring = serializers.BooleanField(source='monitoring_enabled')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Device
        fields = ['id', 'name', 'ipAddress', 'type', 'status', 'monitoring', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'status', 'createdAt', 'updatedAt']

    def create(self, validated_data):
        device = super().create(validated_data)
        MonitoringConfiguration.objects.get_or_create(device=device)
        return device


class MonitoringConfigurationSerializer(serializers.ModelSerializer):
    enabled = serializers.BooleanField(source='device.monitoring_enabled', read_only=True)
    intervalSeconds = serializers.IntegerField(source='interval_seconds', allow_null=True)
    snmpEnabled = serializers.BooleanField(source='snmp_enabled')
    snmpVersion = serializers.CharField(source='snmp_version', allow_blank=True, allow_null=True)
    availableMetrics = serializers.ListField(source='available_metrics', child=serializers.CharField())

    class Meta:
        model = MonitoringConfiguration
        fields = ['enabled', 'intervalSeconds', 'snmpEnabled', 'snmpVersion', 'availableMetrics']


class MonitoringRecordSerializer(serializers.ModelSerializer):
    deviceId = serializers.UUIDField(source='device_id', read_only=True)
    latencyMs = serializers.FloatField(source='latency_ms', allow_null=True)
    packetLossPercent = serializers.FloatField(source='packet_loss_percent', allow_null=True)

    class Meta:
        model = MonitoringRecord
        fields = ['id', 'deviceId', 'timestamp', 'reachable', 'latencyMs', 'packetLossPercent']
        read_only_fields = ['id', 'deviceId']


class HistoricalMonitoringRecordSerializer(MonitoringRecordSerializer):
    deviceName = serializers.CharField(source='device.name', read_only=True)

    class Meta(MonitoringRecordSerializer.Meta):
        fields = MonitoringRecordSerializer.Meta.fields + ['deviceName']


class FaultSerializer(serializers.ModelSerializer):
    device = serializers.PrimaryKeyRelatedField(queryset=Device.objects.all(), write_only=True)
    deviceId = serializers.UUIDField(source='device_id', read_only=True)
    deviceName = serializers.CharField(source='device.name', read_only=True)
    faultType = serializers.ChoiceField(source='fault_type', choices=FaultEvent.FaultType.choices)
    detectedAt = serializers.DateTimeField(source='detected_at')
    resolvedAt = serializers.DateTimeField(source='resolved_at', allow_null=True, read_only=True)
    severity = serializers.ChoiceField(choices=FaultEvent.Severity.choices)
    status = serializers.ChoiceField(choices=FaultEvent.Status.choices)

    class Meta:
        model = FaultEvent
        fields = [
            'id', 'device', 'deviceId', 'deviceName', 'faultType', 'severity',
            'detectedAt', 'status', 'description', 'resolvedAt',
        ]
        read_only_fields = ['id', 'deviceId', 'deviceName', 'resolvedAt']


class NotificationSerializer(serializers.ModelSerializer):
    faultId = serializers.UUIDField(source='fault_id', read_only=True)
    deviceId = serializers.UUIDField(source='fault.device_id', read_only=True)
    deviceName = serializers.CharField(source='fault.device.name', read_only=True)
    faultType = serializers.CharField(source='fault.fault_type', read_only=True)
    severity = serializers.CharField(source='fault.severity', read_only=True)
    detectedAt = serializers.DateTimeField(source='fault.detected_at', read_only=True)
    description = serializers.CharField(source='fault.description', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'faultId', 'deviceId', 'deviceName', 'faultType',
            'severity', 'detectedAt', 'status', 'description',
        ]
        read_only_fields = [
            'id', 'faultId', 'deviceId', 'deviceName', 'faultType',
            'severity', 'detectedAt', 'description',
        ]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = attrs['username'].strip()
        username = identifier

        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user is None:
                raise serializers.ValidationError('Invalid username or password.')
            username = user.get_username()

        user = authenticate(username=username, password=attrs['password'])
        if user is None or not user.is_active or not user.is_staff:
            raise serializers.ValidationError('Invalid username or password.')

        attrs['user'] = user
        return attrs
