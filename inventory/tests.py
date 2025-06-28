from django.test import TestCase
from .models import Device, Interface, Connection, Tag, AlertProfile, Host


class DeviceModelTest(TestCase):
    def test_str(self):
        device = Device(hostname='sw1')
        self.assertEqual(str(device), 'sw1')


class TaggingTest(TestCase):
    def test_device_tag_relationship(self):
        device = Device.objects.create(hostname='sw1')
        tag = Tag.objects.create(name='core-switch')
        device.tags.add(tag)
        self.assertIn(tag, device.tags.all())


class AlertProfileLinkTest(TestCase):
    def test_alert_profile_links(self):
        device = Device.objects.create(hostname='r1')
        tag = Tag.objects.create(name='router')
        profile = AlertProfile.objects.create(name='Default', cpu_threshold=90)
        profile.devices.add(device)
        profile.tags.add(tag)
        self.assertIn(device, profile.devices.all())
        self.assertIn(tag, profile.tags.all())

from unittest.mock import patch
from . import snmp as snmp_module


class SNMPScanTest(TestCase):
    def test_scan_device_creates_interfaces(self):
        def fake_walk(oid, ip, community, *args, **kwargs):
            if oid == snmp_module.IF_NAME_OID:
                return iter([
                    (f"{oid}.1", "Gig0/1"),
                    (f"{oid}.2", "Gig0/2"),
                ])
            if oid == snmp_module.IF_MAC_OID:
                return iter([
                    (f"{oid}.1", "aa:aa:aa:aa:aa:aa"),
                    (f"{oid}.2", "bb:bb:bb:bb:bb:bb"),
                ])
            if oid == snmp_module.IF_STATUS_OID:
                return iter([
                    (f"{oid}.1", 1),
                    (f"{oid}.2", 2),
                ])
            return iter([])

        with patch.object(snmp_module, "snmp_get", side_effect=["sw1", "VendorOS"]), patch.object(
            snmp_module, "snmp_walk", side_effect=fake_walk
        ):
            device = snmp_module.scan_device("192.0.2.1")

        self.assertIsNotNone(device)
        self.assertEqual(device.hostname, "sw1")
        self.assertEqual(device.interfaces.count(), 2)


class NeighborDiscoveryTest(TestCase):
    def test_discover_neighbors_creates_connections(self):
        device = Device.objects.create(hostname="sw1", management_ip="192.0.2.1")
        Interface.objects.create(device=device, name="Gig0/1")

        def fake_walk(oid, ip, community, *args, **kwargs):
            if oid == snmp_module.IF_NAME_OID:
                return iter([(f"{oid}.1", "Gig0/1")])
            if oid == snmp_module.LLDP_SYSNAME_OID:
                return iter([(f"{oid}.1.1", "sw2")])
            if oid == snmp_module.LLDP_PORTID_OID:
                return iter([(f"{oid}.1.1", "Eth0/1")])
            return iter([])

        with patch.object(snmp_module, "snmp_walk", side_effect=fake_walk):
            snmp_module.discover_neighbors("192.0.2.1")

        self.assertEqual(Connection.objects.count(), 1)
        conn = Connection.objects.first()
        self.assertEqual(conn.interface_b.device.hostname, "sw2")

from unittest.mock import MagicMock
from . import ssh as ssh_module


class SSHScanTest(TestCase):
    def test_ssh_scan_device_creates_interfaces(self):
        fake_conn = MagicMock()
        fake_conn.send_command.side_effect = [
            "Hostname: sw1\nVersion 15.1",
            "Gig0/0 10.0.0.1 up up\nGig0/1 unassigned up down",
        ]
        with patch("inventory.ssh.ConnectHandler", return_value=fake_conn):
            device = ssh_module.ssh_scan_device("192.0.2.1", "admin", "pass")

        self.assertEqual(device.hostname, "sw1")
        self.assertEqual(device.interfaces.count(), 2)
        names = sorted(i.name for i in device.interfaces.all())
        self.assertEqual(names, ["Gig0/0", "Gig0/1"])


class CamArpTest(TestCase):
    def test_gather_cam_arp_creates_host(self):
        device = Device.objects.create(hostname="sw1", management_ip="192.0.2.1")
        Interface.objects.create(device=device, name="Gig0/1")

        def fake_walk(oid, ip, community, *args, **kwargs):
            if oid == snmp_module.IF_NAME_OID:
                return iter([(f"{oid}.1", "Gig0/1")])
            if oid == snmp_module.DOT1D_BASE_PORT_IFINDEX_OID:
                return iter([(f"{oid}.1", 1)])
            if oid == snmp_module.DOT1D_TP_FDB_PORT_OID:
                return iter([(f"{oid}.0.17.34.51.68.85", 1)])
            if oid == snmp_module.IP_NET_TO_MEDIA_PHYSADDR_OID:
                return iter([(f"{oid}.1.192.0.2.100", b"\x00\x11\x22\x33\x44\x55")])
            return iter([])

        with patch.object(snmp_module, "snmp_walk", side_effect=fake_walk):
            snmp_module.gather_cam_arp("192.0.2.1")

        host = Host.objects.get(mac_address="00:11:22:33:44:55")
        self.assertEqual(host.ip_address, "192.0.2.100")
        self.assertEqual(host.interface.name, "Gig0/1")
