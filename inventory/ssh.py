from django.utils import timezone
from netmiko import ConnectHandler
from .models import Device, Interface


def ssh_scan_device(ip, username, password, device_type="cisco_ios"):
    """Discover a device via SSH/Telnet and update models."""
    conn = ConnectHandler(device_type=device_type, host=ip, username=username, password=password)
    try:
        version_output = conn.send_command("show version")
        iface_output = conn.send_command("show ip interface brief")
    finally:
        conn.disconnect()

    hostname = None
    for line in version_output.splitlines():
        if line.lower().startswith("hostname") or "name:" in line.lower():
            hostname = line.split()[-1]
            break

    device, _ = Device.objects.get_or_create(management_ip=ip)
    if hostname:
        device.hostname = hostname
    device.discovered_ssh_username = username
    device.discovered_ssh_password = password
    device.last_seen = timezone.now()
    device.last_scanned = timezone.now()
    device.save()

    for line in iface_output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and not line.lower().startswith("interface"):
            name = parts[0]
            ip_addr = parts[1] if parts[1].lower() != "unassigned" else None
            iface, _ = Interface.objects.get_or_create(device=device, name=name)
            iface.ip_address = ip_addr
            iface.last_scanned = timezone.now()
            iface.save()

    return device
