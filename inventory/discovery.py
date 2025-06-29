import ipaddress

# Only scan addresses within these RFC1918 private ranges
PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _is_private(ip):
    """Return True if *ip* is within one of the RFC1918 ranges."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in PRIVATE_NETWORKS)

from django.conf import settings
from .snmp import (
    scan_device,
    discover_neighbors,
    gather_cam_arp,
    discover_ospf_neighbors,
    discover_ospfv3_neighbors,
    discover_bgp_neighbors,
)
from .models import Host, Device
from .server import discover_local_server

DEFAULT_COMMUNITY = "public"


def _get_modules():
    modules = getattr(settings, "DISCOVERY_MODULES", ["arp", "cdp", "lldp"])
    return {m.strip().lower() for m in modules}


def _crawl_network(seed_ips, community=DEFAULT_COMMUNITY):
    """Discover devices starting from a list of seed IPs."""
    discover_local_server()

    visited = set()
    queue = [ip for ip in seed_ips if ip]

    while queue:
        ip = queue.pop(0)
        if ip in visited:
            continue
        if not _is_private(ip):
            continue

        device = scan_device(ip, community)
        if device is None:
            # device unreachable or SNMP failed
            continue

        visited.add(ip)
        modules = _get_modules()
        if {"cdp", "lldp"} & modules:
            discover_neighbors(ip, community)
        if "arp" in modules:
            gather_cam_arp(ip, community)
        new_ips = []
        if "ospf" in modules:
            new_ips.extend(discover_ospf_neighbors(ip, community))
        if "ospfv3" in modules:
            new_ips.extend(discover_ospfv3_neighbors(ip, community))
        if "bgp" in modules:
            new_ips.extend(discover_bgp_neighbors(ip, community))

        hosts = Host.objects.filter(interface__device=device).values_list(
            "ip_address", flat=True
        )
        for host_ip in hosts:
            if host_ip and host_ip not in visited and _is_private(host_ip):
                queue.append(host_ip)
        for n_ip in new_ips:
            if n_ip and n_ip not in visited and _is_private(n_ip):
                queue.append(n_ip)

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
            if ip and _is_private(ip)
        )

    seeds.extend(
        ip
        for ip in Device.objects.exclude(management_ip__isnull=True)
        .exclude(management_ip="")
        .values_list("management_ip", flat=True)
        if ip
    )

    return _crawl_network(seeds, community)

