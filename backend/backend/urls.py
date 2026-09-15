from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', include('network.api.urls')),
    path('api/', include('network.urls')),
]
