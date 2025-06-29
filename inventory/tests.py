from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Device, Interface, Connection, Tag, AlertProfile, Host, MetricRecord, Alert
import subprocess


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

from unittest.mock import patch, mock_open
from . import snmp as snmp_module
from . import tasks
from . import server


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


class PingFallbackTest(TestCase):
    def test_scan_device_adds_host_when_pingable(self):
        with patch.object(snmp_module, "snmp_get", side_effect=[None, None]), \
             patch.object(snmp_module, "check_ping", return_value=True):
            device = snmp_module.scan_device("192.0.2.1")

        self.assertIsNotNone(device)
        self.assertEqual(device.hostname, "192.0.2.1")
        self.assertTrue(device.is_online)


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


from . import discovery as discovery_module


class DiscoveryLogicTest(TestCase):
    def test_discover_network_recurses(self):
        created = {}

        def fake_scan(ip, community="public"):
            device = Device.objects.create(hostname=f"dev-{ip}", management_ip=ip)
            Interface.objects.create(device=device, name="eth0")
            created[ip] = device
            return device

        def fake_gather_cam_arp(ip, community="public"):
            if ip == "10.0.0.1":
                iface = created[ip].interfaces.first()
                Host.objects.create(mac_address="aa", ip_address="10.0.0.2", interface=iface)

        with patch.object(discovery_module, "scan_device", side_effect=fake_scan), \
             patch.object(discovery_module, "discover_neighbors", return_value=None), \
             patch.object(discovery_module, "gather_cam_arp", side_effect=fake_gather_cam_arp), \
             patch.object(discovery_module, "discover_local_server", return_value=None):
            visited = discovery_module.discover_network("10.0.0.1")
        self.assertEqual(set(visited), {"10.0.0.1", "10.0.0.2"})

    def test_local_arp_seeds_are_filtered(self):
        created = {}

        def fake_scan(ip, community="public"):
            device = Device.objects.create(hostname=f"dev-{ip}", management_ip=ip)
            Interface.objects.create(device=device, name="eth0")
            created[ip] = device
            return device

        created_srv = {}

        def fake_discover_local_server():
            if created_srv:
                return created_srv["srv"]
            srv = Device.objects.create(hostname="srv", management_ip="10.0.0.100")
            iface = Interface.objects.create(device=srv, name="eth0")
            Host.objects.create(mac_address="bb", ip_address="10.0.0.5", interface=iface)
            Host.objects.create(mac_address="cc", ip_address="8.8.8.8", interface=iface)
            created_srv["srv"] = srv
            return srv

        with patch.object(discovery_module, "scan_device", side_effect=fake_scan), \
             patch.object(discovery_module, "discover_neighbors", return_value=None), \
             patch.object(discovery_module, "gather_cam_arp", return_value=None), \
             patch.object(discovery_module, "discover_local_server", side_effect=fake_discover_local_server):
            visited = discovery_module.periodic_scan()

        self.assertIn("10.0.0.5", visited)
        self.assertNotIn("8.8.8.8", visited)


class ServerDiscoveryTest(TestCase):
    def test_proc_net_arp_fallback(self):
        arp_data = (
            "IP address       HW type     Flags       HW address            Mask     Device\n"
            "10.0.0.5       0x1         0x2         aa:bb:cc:dd:ee:ff     *        eth0\n"
        )

        real_check_output = subprocess.check_output

        def fake_check_output(cmd, *args, **kwargs):
            if isinstance(cmd, list) and cmd and cmd[0] == "ip":
                if len(cmd) > 1 and cmd[1] == "neigh":
                    raise FileNotFoundError
                if cmd[:3] == ["ip", "-o", "link"]:
                    return "2: eth0: <BROADCAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000 link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff"
                if cmd[:5] == ["ip", "-f", "inet", "addr", "show"]:
                    return "    inet 10.0.0.2/24 brd 10.0.0.255 scope global eth0"
                return ""
            return real_check_output(cmd, *args, **kwargs)

        with patch("subprocess.check_output", side_effect=fake_check_output), \
             patch("inventory.server.open", mock_open(read_data=arp_data), create=True), \
             patch("inventory.server.gather_cam_arp"), \
             patch("socket.gethostname", return_value="srv"), \
             patch("socket.gethostbyname", return_value="10.0.0.2"):
            device = server.discover_local_server()

        host = Host.objects.get(mac_address="aa:bb:cc:dd:ee:ff")
        self.assertEqual(host.ip_address, "10.0.0.5")
        self.assertEqual(host.interface.device, device)


class TopologyDataTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 't@example.com', 'pw')

    def test_topology_data_returns_graph(self):
        d1 = Device.objects.create(hostname='a')
        d2 = Device.objects.create(hostname='b')
        i1 = Interface.objects.create(device=d1, name='eth0')
        i2 = Interface.objects.create(device=d2, name='eth0')
        Connection.objects.create(interface_a=i1, interface_b=i2)

        self.client.force_login(self.user)
        resp = self.client.get(reverse('topology_data'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(len(data['edges']), 1)


class MetricAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 't@example.com', 'pw')

    def test_device_metric_endpoint(self):
        device = Device.objects.create(hostname='r1')
        MetricRecord.objects.create(device=device, metric='cpu', value=50)

        self.client.force_login(self.user)
        resp = self.client.get(reverse('device_metric_data', args=[device.pk, 'cpu']))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)


class InterfaceMetricAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 't@example.com', 'pw')

    def test_interface_metric_endpoint(self):
        device = Device.objects.create(hostname='r1')
        iface = Interface.objects.create(device=device, name='eth0')
        MetricRecord.objects.create(device=device, interface=iface, metric='in_octets', value=100)
        MetricRecord.objects.create(device=device, interface=iface, metric='out_octets', value=200)

        self.client.force_login(self.user)
        resp = self.client.get(reverse('interface_metric_data', args=[iface.pk]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['in']), 1)
        self.assertEqual(len(data['out']), 1)


class InterfaceDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 't@example.com', 'pw')

    def test_interface_detail_view(self):
        device = Device.objects.create(hostname='r1')
        iface = Interface.objects.create(device=device, name='eth0')
        self.client.force_login(self.user)
        resp = self.client.get(reverse('interface_detail', args=[iface.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'eth0')


class AlertListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 't@example.com', 'pw')

    def test_alert_list_view(self):
        device = Device.objects.create(hostname='r1')
        Alert.objects.create(device=device, metric='cpu', value=95, threshold=90)
        self.client.force_login(self.user)
        resp = self.client.get(reverse('alert_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'r1')


class MetricPollingTaskTest(TestCase):
    @patch('inventory.tasks.poll_metrics')
    def test_metric_poll_task_creates_metric_records(self, mock_poll):
        device = Device.objects.create(hostname='r1', management_ip='192.0.2.1')
        Interface.objects.create(device=device, name='eth0')
        mock_poll.return_value = {
            'cpu': 50,
            'memory': 70,
            'interfaces': {'eth0': {'in_octets': 1000, 'out_octets': 2000}},
        }

        tasks.metric_poll_task()

        self.assertEqual(MetricRecord.objects.filter(device=device, metric='cpu').count(), 1)
        self.assertEqual(MetricRecord.objects.filter(device=device, metric='memory').count(), 1)
        self.assertEqual(
            MetricRecord.objects.filter(interface__name='eth0', metric='in_octets').count(),
            1,
        )


class AlertEvaluationTest(TestCase):
    @patch('inventory.tasks.poll_metrics')
    def test_cpu_alert_created_and_cleared(self, mock_poll):
        device = Device.objects.create(hostname='r1', management_ip='192.0.2.1')
        profile = AlertProfile.objects.create(name='default', cpu_threshold=80)
        profile.devices.add(device)

        mock_poll.return_value = {'cpu': 90, 'interfaces': {}}
        tasks.metric_poll_task()
        alert = Alert.objects.filter(device=device, metric='cpu', cleared_at__isnull=True).first()
        self.assertIsNotNone(alert)

        mock_poll.return_value = {'cpu': 50, 'interfaces': {}}
        tasks.metric_poll_task()
        alert.refresh_from_db()
        self.assertIsNotNone(alert.cleared_at)


class DeviceDetailHostsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 't@example.com', 'pw')

    def test_device_detail_displays_hosts(self):
        device = Device.objects.create(hostname='r1')
        iface = Interface.objects.create(device=device, name='eth0')
        Host.objects.create(mac_address='aa:bb:cc:dd:ee:ff', ip_address='10.0.0.2', interface=iface)

        self.client.force_login(self.user)
        resp = self.client.get(reverse('device_detail', args=[device.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'aa:bb:cc:dd:ee:ff')
        self.assertContains(resp, '10.0.0.2')
