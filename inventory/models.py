from django.db import models


class Device(models.Model):
    hostname = models.CharField(max_length=255)
    management_ip = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, blank=True, null=True)
    vendor = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    os_version = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.hostname or str(self.pk)
