from django.test import TestCase
from .models import Device


class DeviceModelTest(TestCase):
    def test_str(self):
        device = Device(hostname='sw1')
        self.assertEqual(str(device), 'sw1')
