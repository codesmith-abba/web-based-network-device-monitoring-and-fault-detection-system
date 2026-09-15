from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDay, TruncHour, TruncMinute
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FaultEvent, MonitoringRecord
from .serializers import FaultSerializer, HistoricalMonitoringRecordSerializer


MAX_HISTORY_RECORDS = 500
MAX_AGGREGATION_BUCKETS = 1000
MAX_RANGE_DAYS = 366


def _parse_range(request, field_name):
    value = request.query_params.get(field_name)
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError(f'Invalid {field_name} datetime. Use an ISO-8601 datetime.')
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _apply_date_range(queryset, request, field):
    start = _parse_range(request, 'from')
    end = _parse_range(request, 'to')

    if start and end and start > end:
        raise ValueError('The from datetime must be earlier than or equal to the to datetime.')
    if start and end and end - start > timedelta(days=MAX_RANGE_DAYS):
        raise ValueError(f'Date ranges cannot exceed {MAX_RANGE_DAYS} days.')

    if start:
        queryset = queryset.filter(**{f'{field}__gte': start})
    if end:
        queryset = queryset.filter(**{f'{field}__lte': end})
    return queryset


def _parse_limit(request, maximum=MAX_HISTORY_RECORDS):
    value = request.query_params.get('limit')
    if value is None:
        return maximum
    try:
        return max(1, min(maximum, int(value)))
    except (TypeError, ValueError):
        raise ValueError(f'limit must be an integer between 1 and {maximum}.')


def _monitoring_bucket_expression(aggregation):
    expressions = {
        'minute': TruncMinute('timestamp'),
        'hour': TruncHour('timestamp'),
        'day': TruncDay('timestamp'),
    }
    try:
        return expressions[aggregation]
    except KeyError as exc:
        raise ValueError('aggregation must be one of: minute, hour, day.') from exc


class MonitoringHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            limit = _parse_limit(request)
            queryset = MonitoringRecord.objects.select_related('device').all()
            device_id = request.query_params.get('deviceId')
            if device_id:
                queryset = queryset.filter(device_id=device_id)
            reachable = request.query_params.get('reachable')
            if reachable is not None:
                if reachable.lower() not in {'true', 'false'}:
                    raise ValueError('reachable must be true or false.')
                queryset = queryset.filter(reachable=reachable.lower() == 'true')
            queryset = _apply_date_range(queryset, request, 'timestamp')

            aggregation = request.query_params.get('aggregation')
            if not aggregation:
                records = list(queryset.order_by('-timestamp')[:limit])
                return Response({
                    'records': HistoricalMonitoringRecordSerializer(records, many=True).data,
                    'meta': {
                        'mode': 'raw',
                        'count': len(records),
                        'limit': limit,
                    },
                })

            bucket_expression = _monitoring_bucket_expression(aggregation)
            buckets = list(
                queryset
                .annotate(bucket=bucket_expression)
                .values('bucket')
                .annotate(
                    records=Count('id'),
                    reachable_records=Count('id', filter=Q(reachable=True)),
                    average_latency_ms=Avg('latency_ms'),
                    average_packet_loss_percent=Avg('packet_loss_percent'),
                )
                .order_by('-bucket')[:MAX_AGGREGATION_BUCKETS]
            )

            serialized = []
            for bucket in reversed(buckets):
                total = bucket['records']
                reachable_count = bucket['reachable_records']
                serialized.append({
                    'timestamp': bucket['bucket'],
                    'records': total,
                    'reachableRecords': reachable_count,
                    'unreachableRecords': total - reachable_count,
                    'availabilityPercent': round(reachable_count / total * 100, 2) if total else None,
                    'averageLatencyMs': round(bucket['average_latency_ms'], 3) if bucket['average_latency_ms'] is not None else None,
                    'averagePacketLossPercent': round(bucket['average_packet_loss_percent'], 3) if bucket['average_packet_loss_percent'] is not None else None,
                })

            return Response({
                'buckets': serialized,
                'meta': {
                    'mode': 'aggregated',
                    'aggregation': aggregation,
                    'count': len(serialized),
                    'limit': MAX_AGGREGATION_BUCKETS,
                },
            })
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class FaultHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            limit = _parse_limit(request)
            queryset = FaultEvent.objects.select_related('device').all()

            filters = {
                'deviceId': 'device_id',
                'severity': 'severity',
                'status': 'status',
                'faultType': 'fault_type',
            }
            for key, field in filters.items():
                value = request.query_params.get(key)
                if value:
                    queryset = queryset.filter(**{field: value})

            queryset = _apply_date_range(queryset, request, 'detected_at')
            aggregation = request.query_params.get('aggregation')

            if not aggregation:
                faults = list(queryset.order_by('-detected_at')[:limit])
                return Response({
                    'faults': FaultSerializer(faults, many=True).data,
                    'meta': {
                        'mode': 'raw',
                        'count': len(faults),
                        'limit': limit,
                    },
                })

            if aggregation != 'day':
                raise ValueError('Fault aggregation currently supports: day.')

            buckets = list(
                queryset
                .annotate(bucket=TruncDay('detected_at'))
                .values('bucket')
                .annotate(
                    faults=Count('id'),
                    active=Count('id', filter=Q(status=FaultEvent.Status.ACTIVE)),
                    acknowledged=Count('id', filter=Q(status=FaultEvent.Status.ACKNOWLEDGED)),
                    resolved=Count('id', filter=Q(status=FaultEvent.Status.RESOLVED)),
                    critical=Count('id', filter=Q(severity=FaultEvent.Severity.CRITICAL)),
                    high=Count('id', filter=Q(severity=FaultEvent.Severity.HIGH)),
                    medium=Count('id', filter=Q(severity=FaultEvent.Severity.MEDIUM)),
                    low=Count('id', filter=Q(severity=FaultEvent.Severity.LOW)),
                )
                .order_by('-bucket')[:MAX_AGGREGATION_BUCKETS]
            )

            serialized = []
            for bucket in reversed(buckets):
                serialized.append({
                    'timestamp': bucket['bucket'],
                    'faults': bucket['faults'],
                    'status': {
                        'active': bucket['active'],
                        'acknowledged': bucket['acknowledged'],
                        'resolved': bucket['resolved'],
                    },
                    'severity': {
                        'critical': bucket['critical'],
                        'high': bucket['high'],
                        'medium': bucket['medium'],
                        'low': bucket['low'],
                    },
                })

            return Response({
                'buckets': serialized,
                'meta': {
                    'mode': 'aggregated',
                    'aggregation': aggregation,
                    'count': len(serialized),
                    'limit': MAX_AGGREGATION_BUCKETS,
                },
            })
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
