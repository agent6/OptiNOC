from .snmp import scan_device, discover_neighbors, gather_cam_arp
from .models import Host, Device
from .server import discover_local_server

DEFAULT_COMMUNITY = "public"


def discover_network(seed_ip, community=DEFAULT_COMMUNITY):
    """Iteratively discover network starting from seed_ip.
    Returns a list of visited IP addresses.
    """
    discover_local_server()

    visited = set()
    queue = [seed_ip]

    while queue:
        ip = queue.pop(0)
        if ip in visited:
            continue

        device = scan_device(ip, community)
        if device is None:
            # device unreachable or SNMP failed
            continue

        visited.add(ip)
        discover_neighbors(ip, community)
        gather_cam_arp(ip, community)

        hosts = Host.objects.filter(interface__device=device).values_list(
            "ip_address", flat=True
        )
        for host_ip in hosts:
            if host_ip and host_ip not in visited:
                queue.append(host_ip)

    return list(visited)


def periodic_scan(community=DEFAULT_COMMUNITY):
    """Rescan all known devices to refresh inventory."""
    discover_local_server()

    scanned = []
    for device in Device.objects.all():
        if not device.management_ip:
            continue
        scan_device(device.management_ip, community)
        discover_neighbors(device.management_ip, community)
        gather_cam_arp(device.management_ip, community)
        scanned.append(device.management_ip)
    return scanned

