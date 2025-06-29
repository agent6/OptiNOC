from django.shortcuts import render, redirect
from django.db.models import Prefetch
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from .serializers import MetricRecordSerializer
from .models import Device, Interface, Connection, Tag, Alert
from .forms import DeviceTagForm, DeviceCredentialsForm
from django.contrib.auth.decorators import login_required
from .tasks import periodic_scan_task


@login_required
def device_list(request):
    devices = Device.objects.all().prefetch_related('tags')
    tag = request.GET.get('tag')
    if tag:
        devices = devices.filter(tags__name=tag)
    vendor = request.GET.get('vendor')
    if vendor:
        devices = devices.filter(vendor__icontains=vendor)
    search = request.GET.get('q')
    if search:
        devices = devices.filter(hostname__icontains=search)
    tags = Tag.objects.all()
    return render(request, 'inventory/device_list.html', {
        'devices': devices,
        'tags': tags,
    })


@login_required
def trigger_discovery(request):
    """Kick off an inventory scan via Celery and redirect back."""
    if request.method == "POST":
        periodic_scan_task.delay()
    return redirect('device_list')


@login_required
def device_detail(request, pk):
    device = Device.objects.prefetch_related('interfaces__hosts', 'tags').get(pk=pk)

    if request.method == "POST":
        form = DeviceTagForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            return redirect('device_detail', pk=pk)
    else:
        form = DeviceTagForm(instance=device)

    connections = Connection.objects.filter(
        interface_a__device=device
    ).select_related('interface_b__device') | Connection.objects.filter(
        interface_b__device=device
    ).select_related('interface_a__device')
    return render(request, 'inventory/device_detail.html', {
        'device': device,
        'connections': connections,
        'form': form,
    })


@login_required
def device_credentials(request, pk):
    """Allow entering SNMP/SSH credentials and roadblocks."""
    device = Device.objects.get(pk=pk)
    if request.method == "POST":
        form = DeviceCredentialsForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            return redirect('device_detail', pk=pk)
    else:
        form = DeviceCredentialsForm(instance=device)
    return render(request, 'inventory/device_credentials.html', {
        'device': device,
        'form': form,
    })


@login_required
def interface_detail(request, pk):
    """Display metrics and details for a single interface."""
    iface = Interface.objects.select_related('device').prefetch_related('hosts').get(pk=pk)
    return render(request, 'inventory/interface_detail.html', {
        'interface': iface,
    })


@login_required
def network_topology(request):
    """Render the topology visualization page."""
    return render(request, 'inventory/network_topology.html')


@login_required
def topology_data(request):
    """Return nodes and edges for the topology diagram as JSON."""
    nodes = [
        {'id': d.pk, 'label': d.hostname}
        for d in Device.objects.all()
    ]
    edges = [
        {
            'from': c.interface_a.device_id,
            'to': c.interface_b.device_id,
        }
        for c in Connection.objects.select_related(
            'interface_a__device', 'interface_b__device'
        )
    ]
    return JsonResponse({'nodes': nodes, 'edges': edges})


@api_view(['GET'])
def device_metric_data(request, pk, metric):
    """Return time-series metric data for a device."""
    device = Device.objects.get(pk=pk)
    records = device.metric_records.filter(metric=metric)

    start = request.GET.get('start')
    end = request.GET.get('end')
    if start:
        dt = parse_datetime(start)
        if dt:
            records = records.filter(timestamp__gte=dt)
    if end:
        dt = parse_datetime(end)
        if dt:
            records = records.filter(timestamp__lte=dt)

    records = records.order_by('timestamp')
    serializer = MetricRecordSerializer(records, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def interface_metric_data(request, pk):
    """Return in/out octet metrics for an interface."""
    iface = Interface.objects.get(pk=pk)
    records = iface.metric_records.filter(metric__in=["in_octets", "out_octets"])

    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        dt = parse_datetime(start)
        if dt:
            records = records.filter(timestamp__gte=dt)
    if end:
        dt = parse_datetime(end)
        if dt:
            records = records.filter(timestamp__lte=dt)

    in_records = records.filter(metric="in_octets").order_by("timestamp")
    out_records = records.filter(metric="out_octets").order_by("timestamp")
    data = {
        "in": MetricRecordSerializer(in_records, many=True).data,
        "out": MetricRecordSerializer(out_records, many=True).data,
    }
    return Response(data)


@login_required
def alert_list(request):
    """Display active alerts and recent history."""
    active = Alert.objects.filter(cleared_at__isnull=True).select_related("device")
    history = (
        Alert.objects.filter(cleared_at__isnull=False)
        .select_related("device")
        .order_by("-timestamp")[:50]
    )
    return render(
        request,
        "inventory/alerts.html",
        {"active_alerts": active, "history": history},
    )
