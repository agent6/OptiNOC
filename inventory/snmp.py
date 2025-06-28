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
from django.utils import timezone
from .models import Device, Interface, Connection


DEFAULT_COMMUNITY = "public"
DEFAULT_PORT = 161


def snmp_get(oid, target, community=DEFAULT_COMMUNITY, port=DEFAULT_PORT, timeout=1, retries=0):
    """Perform a simple SNMP GET request and return the value or None on failure."""
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

