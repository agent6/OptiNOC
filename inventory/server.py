import re
import socket
import platform
import subprocess
from django.utils import timezone
from .models import Device, Interface, Host
from .snmp import gather_cam_arp


def discover_local_server():
    """Add the server running OptiNOC as a Device and parse local ARP table."""
    hostname = socket.gethostname()
    try:
        route = subprocess.check_output(['ip', 'route', 'show', 'default'], text=True).strip()
    except Exception:
        route = ''
    default_iface = None
    if ' dev ' in f' {route} ':
        parts = route.split()
        for i, part in enumerate(parts):
            if part == 'dev' and i + 1 < len(parts):
                default_iface = parts[i + 1]
                break
    mgmt_ip = None
    if default_iface:
        try:
            addr_out = subprocess.check_output(['ip', '-f', 'inet', 'addr', 'show', default_iface], text=True)
            m = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', addr_out)
            if m:
                mgmt_ip = m.group(1)
        except Exception:
            pass
    if mgmt_ip is None:
        try:
            mgmt_ip = socket.gethostbyname(hostname)
        except Exception:
            pass

    device, _ = Device.objects.get_or_create(hostname=hostname)
    changed = False
    if mgmt_ip and device.management_ip != mgmt_ip:
        device.management_ip = mgmt_ip
        changed = True
    vendor = 'Linux'
    os_version = platform.platform()
    if device.vendor != vendor:
        device.vendor = vendor
        changed = True
    if device.os_version != os_version:
        device.os_version = os_version
        changed = True
    if changed:
        device.last_seen = timezone.now()
        device.save()

    try:
        link_out = subprocess.check_output(['ip', '-o', 'link'], text=True)
        for line in link_out.splitlines():
            m = re.match(r'\d+: ([^:]+):.*link/[^ ]+ ([0-9a-f:]{17}|00:00:00:00:00:00)', line)
            if not m:
                continue
            name, mac = m.groups()
            iface, _ = Interface.objects.get_or_create(device=device, name=name)
            iface.mac_address = mac
            ip_addr = None
            try:
                addr_out = subprocess.check_output(['ip', '-f', 'inet', 'addr', 'show', name], text=True)
                m2 = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', addr_out)
                if m2:
                    ip_addr = m2.group(1)
            except Exception:
                pass
            iface.ip_address = ip_addr
            iface.last_scanned = timezone.now()
            iface.save()
    except Exception:
        pass

    try:
        neigh_out = subprocess.check_output(['ip', 'neigh'], text=True)
        for line in neigh_out.splitlines():
            parts = line.split()
            if len(parts) >= 6 and parts[2] == 'dev' and parts[4] == 'lladdr':
                ip_addr, if_name, mac = parts[0], parts[3], parts[5]
                iface_obj = device.interfaces.filter(name=if_name).first()
                host, _ = Host.objects.get_or_create(mac_address=mac)
                host.ip_address = ip_addr
                if iface_obj:
                    host.interface = iface_obj
                host.last_seen = timezone.now()
                host.save()
    except Exception:
        pass

    if mgmt_ip:
        try:
            gather_cam_arp(mgmt_ip)
        except Exception:
            pass
    if default_iface and mgmt_ip:
        try:
            gw = None
            if route:
                match = re.search(r'via (\d+\.\d+\.\d+\.\d+)', route)
                if match:
                    gw = match.group(1)
            if gw:
                gather_cam_arp(gw)
        except Exception:
            pass

    return device
