try:
    from pysnmp.hlapi import (
        SnmpEngine,
        CommunityData,
        UdpTransportTarget,
        ContextData,
        ObjectType,
        ObjectIdentity,
        getCmd,
        nextCmd,
    )
except Exception:  # pragma: no cover - fallback for missing pysnmp on Py3.12
    SnmpEngine = CommunityData = UdpTransportTarget = ContextData = None

    def getCmd(*args, **kwargs):  # type: ignore
        raise ImportError("pysnmp is not available")

    def nextCmd(*args, **kwargs):  # type: ignore
        raise ImportError("pysnmp is not available")

    try:
        from puresnmp import Client, V2C, PyWrapper
        import asyncio

        def _pure_client(target, community, port, timeout, retries):
            client = Client(target, V2C(community), port=port)
            client.configure(timeout=timeout, retries=retries)
            return PyWrapper(client)

    except Exception:  # pragma: no cover - no SNMP libraries available
        Client = PyWrapper = None
from django.utils import timezone
from .models import Device, Interface, Connection, Host


DEFAULT_COMMUNITY = "public"
DEFAULT_PORT = 161


def snmp_get(oid, target, community=DEFAULT_COMMUNITY, port=DEFAULT_PORT, timeout=1, retries=0):
    """Perform a simple SNMP GET request and return the value or None on failure."""
    if SnmpEngine is None:
        if Client is None:
            raise ImportError("No SNMP library available")
        async def _run():
            wrapper = _pure_client(target, community, port, timeout, retries)
            return await wrapper.get(oid)

        try:
            return asyncio.run(_run())
        except Exception:
            return None

    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((target, port), timeout=timeout, retries=retries),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    error_indication, error_status, error_index, var_binds = next(iterator)
    if error_indication or error_status:
        return None
    return var_binds[0][1]


def snmp_walk(oid, target, community=DEFAULT_COMMUNITY, port=DEFAULT_PORT, timeout=1, retries=0):
    """Generator yielding OID, value pairs from an SNMP walk."""
    if SnmpEngine is None:
        if Client is None:
            raise ImportError("No SNMP library available")

        async def _run():
            wrapper = _pure_client(target, community, port, timeout, retries)
            results = []
            async for vb in wrapper.walk(oid):
                results.append((str(vb.oid), vb.value))
            return results

        try:
            for item in asyncio.run(_run()):
                yield item
            return
        except Exception:
            return

    for (error_indication, error_status, error_index, var_binds) in nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((target, port), timeout=timeout, retries=retries),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False,
    ):
        if error_indication or error_status:
            break
        for oid_val in var_binds:
            yield str(oid_val[0]), oid_val[1]


SYS_NAME_OID = "1.3.6.1.2.1.1.5.0"
SYS_DESCR_OID = "1.3.6.1.2.1.1.1.0"
IF_NAME_OID = "1.3.6.1.2.1.2.2.1.2"
IF_MAC_OID = "1.3.6.1.2.1.2.2.1.6"
IF_STATUS_OID = "1.3.6.1.2.1.2.2.1.8"

# CAM and ARP table OIDs
DOT1D_TP_FDB_PORT_OID = "1.3.6.1.2.1.17.4.3.1.2"
DOT1D_BASE_PORT_IFINDEX_OID = "1.3.6.1.2.1.17.1.4.1.2"
IP_NET_TO_MEDIA_PHYSADDR_OID = "1.3.6.1.2.1.4.22.1.2"
IP_NET_TO_MEDIA_IFINDEX_OID = "1.3.6.1.2.1.4.22.1.1"
IP_NET_TO_MEDIA_NETADDR_OID = "1.3.6.1.2.1.4.22.1.3"


def scan_device(ip, community=DEFAULT_COMMUNITY):
    """Discover a device via SNMP and update Device/Interface models."""
    sys_name = snmp_get(SYS_NAME_OID, ip, community)
    sys_descr = snmp_get(SYS_DESCR_OID, ip, community)
    if sys_name is None:
        # Device did not respond
        return None

    device, _ = Device.objects.get_or_create(management_ip=ip)
    device.hostname = str(sys_name)
    device.vendor = str(sys_descr).split()[0] if sys_descr else ""
    device.os_version = str(sys_descr)
    device.discovered_snmp_community = community
    device.last_seen = timezone.now()
    device.save()

    # Walk interface table
    names = {}
    for oid, val in snmp_walk(IF_NAME_OID, ip, community):
        # IF-MIB::ifDescr.<index> or ifName
        idx = oid.split(".")[-1]
        names[idx] = str(val)

    macs = {oid.split(".")[-1]: str(val) for oid, val in snmp_walk(IF_MAC_OID, ip, community)}
    statuses = {oid.split(".")[-1]: int(val) for oid, val in snmp_walk(IF_STATUS_OID, ip, community)}

    for idx, name in names.items():
        iface, _ = Interface.objects.get_or_create(device=device, name=name)
        iface.mac_address = macs.get(idx, "")
        iface.status = str(statuses.get(idx, ""))
        iface.last_scanned = timezone.now()
        iface.save()

    device.last_scanned = timezone.now()
    device.save()
    return device


# LLDP and CDP tables
LLDP_SYSNAME_OID = "1.0.8802.1.1.2.1.4.1.1.9"
LLDP_PORTID_OID = "1.0.8802.1.1.2.1.4.1.1.7"
CDP_DEVICEID_OID = "1.3.6.1.4.1.9.9.23.1.2.1.1.6"
CDP_DEVICEPORT_OID = "1.3.6.1.4.1.9.9.23.1.2.1.1.7"


def discover_neighbors(ip, community=DEFAULT_COMMUNITY):
    """Discover neighbors via LLDP/CDP and create Connection records."""
    device = Device.objects.filter(management_ip=ip).first()
    if not device:
        return

    # Map interface indexes to Interface objects
    idx_to_iface = {}
    for oid, val in snmp_walk(IF_NAME_OID, ip, community):
        idx = oid.split(".")[-1]
        iface = Interface.objects.filter(device=device, name=str(val)).first()
        if iface:
            idx_to_iface[idx] = iface

    neighbors = {}

    # LLDP neighbors
    for oid, val in snmp_walk(LLDP_SYSNAME_OID, ip, community):
        local_idx = oid.split(".")[-2]
        neighbors.setdefault(local_idx, {})["hostname"] = str(val)
    for oid, val in snmp_walk(LLDP_PORTID_OID, ip, community):
        local_idx = oid.split(".")[-2]
        neighbors.setdefault(local_idx, {})["port"] = str(val)

    # CDP neighbors
    for oid, val in snmp_walk(CDP_DEVICEID_OID, ip, community):
        local_idx = oid.split(".")[-2]
        neighbors.setdefault(local_idx, {})["hostname"] = str(val)
    for oid, val in snmp_walk(CDP_DEVICEPORT_OID, ip, community):
        local_idx = oid.split(".")[-2]
        neighbors.setdefault(local_idx, {})["port"] = str(val)

    for idx, data in neighbors.items():
        local_iface = idx_to_iface.get(idx)
        if not local_iface:
            continue
        remote_device, _ = Device.objects.get_or_create(hostname=data.get("hostname", ""))
        remote_iface, _ = Interface.objects.get_or_create(device=remote_device, name=data.get("port", ""))
        Connection.objects.get_or_create(interface_a=local_iface, interface_b=remote_iface)


def gather_cam_arp(ip, community=DEFAULT_COMMUNITY):
    """Collect CAM and ARP tables and link hosts to interfaces."""
    device = Device.objects.filter(management_ip=ip).first()
    if not device:
        return

    # Map interface indexes to Interface objects
    idx_to_iface = {}
    for oid, val in snmp_walk(IF_NAME_OID, ip, community):
        idx = oid.split(".")[-1]
        iface = Interface.objects.filter(device=device, name=str(val)).first()
        if iface:
            idx_to_iface[idx] = iface

    # Bridge port -> ifIndex mapping
    bridge_to_if = {oid.split(".")[-1]: str(val) for oid, val in snmp_walk(DOT1D_BASE_PORT_IFINDEX_OID, ip, community)}

    # CAM table entries: map MAC -> ifIndex
    cam_entries = {}
    for oid, val in snmp_walk(DOT1D_TP_FDB_PORT_OID, ip, community):
        mac_parts = oid.split(".")[-6:]
        mac = ":".join(f"{int(p):02x}" for p in mac_parts)
        bridge_port = str(val)
        ifindex = bridge_to_if.get(bridge_port)
        if ifindex:
            cam_entries[mac] = ifindex

    for mac, ifidx in cam_entries.items():
        iface = idx_to_iface.get(ifidx)
        if not iface:
            continue
        host, _ = Host.objects.get_or_create(mac_address=mac)
        host.interface = iface
        host.last_seen = timezone.now()
        host.save()

    # ARP table entries
    for oid, val in snmp_walk(IP_NET_TO_MEDIA_PHYSADDR_OID, ip, community):
        parts = oid.split(".")
        if len(parts) < 5:
            continue
        ifindex = parts[-5]
        ip_addr = ".".join(parts[-4:])
        octets = val.asOctets() if hasattr(val, "asOctets") else val
        mac = ":".join(f"{b:02x}" for b in octets)
        iface = idx_to_iface.get(ifindex)
        host, _ = Host.objects.get_or_create(mac_address=mac)
        host.ip_address = ip_addr
        if iface:
            host.interface = iface
        host.last_seen = timezone.now()
        host.save()


# Performance metric OIDs
CPU_LOAD_OID = "1.3.6.1.2.1.25.3.3.1.2"
MEM_TOTAL_OID = "1.3.6.1.4.1.2021.4.5.0"
MEM_AVAIL_OID = "1.3.6.1.4.1.2021.4.6.0"
IF_IN_OCTETS_OID = "1.3.6.1.2.1.2.2.1.10"
IF_OUT_OCTETS_OID = "1.3.6.1.2.1.2.2.1.16"


def poll_metrics(ip, community=DEFAULT_COMMUNITY):
    """Return basic performance metrics for a device."""

    metrics = {}

    cpu_loads = [int(v) for _, v in snmp_walk(CPU_LOAD_OID, ip, community)]
    if cpu_loads:
        metrics["cpu"] = sum(cpu_loads) / len(cpu_loads)

    mem_total = snmp_get(MEM_TOTAL_OID, ip, community)
    mem_avail = snmp_get(MEM_AVAIL_OID, ip, community)
    if mem_total is not None and mem_avail is not None and int(mem_total) > 0:
        used = int(mem_total) - int(mem_avail)
        metrics["memory"] = used / int(mem_total) * 100

    names = {oid.split(".")[-1]: str(val) for oid, val in snmp_walk(IF_NAME_OID, ip, community)}
    in_octets = {oid.split(".")[-1]: int(val) for oid, val in snmp_walk(IF_IN_OCTETS_OID, ip, community)}
    out_octets = {oid.split(".")[-1]: int(val) for oid, val in snmp_walk(IF_OUT_OCTETS_OID, ip, community)}

    interfaces = {}
    for idx, name in names.items():
        interfaces[name] = {
            "in_octets": in_octets.get(idx),
            "out_octets": out_octets.get(idx),
        }
    metrics["interfaces"] = interfaces

    return metrics


