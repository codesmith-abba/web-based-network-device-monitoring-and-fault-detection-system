from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardView,
    DeviceViewSet,
    FaultHistoryView,
    FaultViewSet,
    LoginView,
    LogoutView,
    MeView,
    MonitoringHistoryView,
    MonitoringRecordViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register('devices', DeviceViewSet, basename='device')
router.register('monitoring-records', MonitoringRecordViewSet, basename='monitoring-record')
router.register('faults', FaultViewSet, basename='fault')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('monitoring-history/', MonitoringHistoryView.as_view(), name='monitoring-history'),
    path('fault-history/', FaultHistoryView.as_view(), name='fault-history'),
    path('', include(router.urls)),
]
