import ipaddress

from .snmp import scan_device, discover_neighbors, gather_cam_arp
from .models import Host, Device
from .server import discover_local_server

DEFAULT_COMMUNITY = "public"


def _crawl_network(seed_ips, community=DEFAULT_COMMUNITY):
    """Discover devices starting from a list of seed IPs."""
    discover_local_server()

    visited = set()
    queue = [ip for ip in seed_ips if ip]

    while queue:
        ip = queue.pop(0)
        if ip in visited:
            continue
        try:
            if not ipaddress.ip_address(ip).is_private:
                continue
        except ValueError:
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
                try:
                    if ipaddress.ip_address(host_ip).is_private:
                        queue.append(host_ip)
                except ValueError:
                    continue

    return list(visited)


def discover_network(seed_ip, community=DEFAULT_COMMUNITY):
    """Iteratively discover network starting from a single seed IP."""
    return _crawl_network([seed_ip], community)


def periodic_scan(community=DEFAULT_COMMUNITY):
    """Rescan known devices and expand discovery based on ARP entries."""
    server = discover_local_server()

    seeds = []
    if server:
        seeds.extend(
            ip
            for ip in Host.objects.filter(interface__device=server).values_list(
                "ip_address", flat=True
            )
            if ip and ipaddress.ip_address(ip).is_private
        )

    seeds.extend(
        ip
        for ip in Device.objects.exclude(management_ip__isnull=True)
        .exclude(management_ip="")
        .values_list("management_ip", flat=True)
        if ip
    )

    return _crawl_network(seeds, community)

