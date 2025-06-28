from django.db import models


class Device(models.Model):
    """Network device or other managed asset."""

    hostname = models.CharField(max_length=255)
    management_ip = models.GenericIPAddressField(
        protocol="both", unpack_ipv4=True, blank=True, null=True
    )
    vendor = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    os_version = models.CharField(max_length=255, blank=True)
    snmp_community = models.CharField(max_length=255, blank=True)
    ssh_username = models.CharField(max_length=255, blank=True)
    ssh_password = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.hostname or str(self.pk)


class Interface(models.Model):
    """Network interface belonging to a device."""

    device = models.ForeignKey(Device, related_name="interfaces", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=32, blank=True)
    ip_address = models.GenericIPAddressField(protocol="both", unpack_ipv4=True, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.device.hostname}:{self.name}" if self.device_id else self.name


class Connection(models.Model):
    """Physical or logical link between two interfaces."""

    interface_a = models.ForeignKey(
        Interface, related_name="link_end_a", on_delete=models.CASCADE
    )
    interface_b = models.ForeignKey(
        Interface, related_name="link_end_b", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.interface_a} <-> {self.interface_b}"


class Tag(models.Model):
    """Label for grouping devices."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class AlertProfile(models.Model):
    """Thresholds for generating alerts."""

    name = models.CharField(max_length=100)
    cpu_threshold = models.PositiveSmallIntegerField(blank=True, null=True)
    interface_down = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
