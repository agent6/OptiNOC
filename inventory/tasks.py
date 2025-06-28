from celery import shared_task
from .discovery import discover_network
from .snmp import scan_device, discover_neighbors, gather_cam_arp


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
