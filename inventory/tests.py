from django.test import TestCase
from .models import Device, Tag, AlertProfile


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
