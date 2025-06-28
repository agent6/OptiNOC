from django.shortcuts import render, redirect
from django.db.models import Prefetch
from .models import Device, Interface, Connection, Tag
from .forms import DeviceTagForm
from django.contrib.auth.decorators import login_required


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
