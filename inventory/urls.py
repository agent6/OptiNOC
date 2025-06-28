from django.urls import path
from . import views

urlpatterns = [
    path('devices/', views.device_list, name='device_list'),
    path('devices/<int:pk>/', views.device_detail, name='device_detail'),
    path('topology/', views.network_topology, name='network_topology'),
    path('topology/data/', views.topology_data, name='topology_data'),
    path('alerts/', views.alert_list, name='alert_list'),
    path('api/devices/<int:pk>/metrics/<str:metric>/',
         views.device_metric_data,
         name='device_metric_data'),
]
