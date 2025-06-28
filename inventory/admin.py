from django.contrib import admin
from .models import Device, Interface, Connection, Tag, AlertProfile


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'management_ip', 'vendor', 'model')


@admin.register(Interface)
class InterfaceAdmin(admin.ModelAdmin):
    list_display = ('device', 'name', 'status')


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('interface_a', 'interface_b')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(AlertProfile)
class AlertProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu_threshold', 'interface_down')
