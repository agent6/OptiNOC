from celery import shared_task
from .discovery import discover_network, periodic_scan
from django.utils import timezone
from .snmp import scan_device, discover_neighbors, gather_cam_arp, poll_metrics
from .models import Device, MetricRecord


@shared_task
def scan_device_task(ip, community="public"):
    """Scan a single device and return discovered host IPs."""
    device = scan_device(ip, community)
    if device is None:
        return []

    discover_neighbors(ip, community)
    gather_cam_arp(ip, community)

    from .models import Host

    return list(
        Host.objects.filter(interface__device=device).values_list("ip_address", flat=True)
    )


@shared_task
def discover_network_task(seed_ip, community="public"):
    """Celery task wrapper for discover_network."""
    return discover_network(seed_ip, community)


@shared_task
def periodic_scan_task(community="public"):
    """Rescan all known devices."""
    return periodic_scan(community)


@shared_task
def metric_poll_task(default_community="public"):
    """Poll devices for performance metrics and store results."""
    results = []
    timestamp = timezone.now()
    for device in Device.objects.all():
        if not device.management_ip:
            continue
        community = device.snmp_community or device.discovered_snmp_community or default_community
        metrics = poll_metrics(device.management_ip, community)

        if "cpu" in metrics:
            MetricRecord.objects.create(
                device=device,
                metric="cpu",
                value=metrics["cpu"],
                timestamp=timestamp,
            )
        if "memory" in metrics:
            MetricRecord.objects.create(
                device=device,
                metric="memory",
                value=metrics["memory"],
                timestamp=timestamp,
            )

        for iface_name, vals in metrics.get("interfaces", {}).items():
            iface = device.interfaces.filter(name=iface_name).first()
            if not iface:
                continue
            if vals.get("in_octets") is not None:
                MetricRecord.objects.create(
                    device=device,
                    interface=iface,
                    metric="in_octets",
                    value=vals["in_octets"],
                    timestamp=timestamp,
                )
            if vals.get("out_octets") is not None:
                MetricRecord.objects.create(
                    device=device,
                    interface=iface,
                    metric="out_octets",
                    value=vals["out_octets"],
                    timestamp=timestamp,
                )

        results.append(device.management_ip)

    return results


@shared_task
def alert_check_task():
    """Placeholder for alert evaluation."""
    # Logic for evaluating alert thresholds will be implemented later
    return "alerts checked"
