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
    # discovery metadata
    last_seen = models.DateTimeField(blank=True, null=True)
    last_scanned = models.DateTimeField(blank=True, null=True)
    discovered_snmp_community = models.CharField(max_length=255, blank=True)
    discovered_ssh_username = models.CharField(max_length=255, blank=True)
    discovered_ssh_password = models.CharField(max_length=255, blank=True)
    roadblocks = models.TextField(blank=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='devices')

    def __str__(self):
        return self.hostname or str(self.pk)


class Interface(models.Model):
    """Network interface belonging to a device."""

    device = models.ForeignKey(Device, related_name="interfaces", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=32, blank=True)
    ip_address = models.GenericIPAddressField(protocol="both", unpack_ipv4=True, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True)
    last_scanned = models.DateTimeField(blank=True, null=True)

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
    devices = models.ManyToManyField('Device', blank=True, related_name='alert_profiles')
    tags = models.ManyToManyField('Tag', blank=True, related_name='alert_profiles')

    def __str__(self):
        return self.name


class Host(models.Model):
    """Host discovered via ARP/CAM tables."""
    mac_address = models.CharField(max_length=32, unique=True)
    ip_address = models.GenericIPAddressField(protocol="both", blank=True, null=True)
    interface = models.ForeignKey(Interface, related_name="hosts", null=True, blank=True, on_delete=models.SET_NULL)
    last_seen = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.mac_address


class MetricRecord(models.Model):
    """Time-series performance metric for a device or interface."""

    device = models.ForeignKey(
        Device,
        related_name="metric_records",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    interface = models.ForeignKey(
        Interface,
        related_name="metric_records",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    metric = models.CharField(max_length=100)
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["device", "interface", "metric", "timestamp"])
        ]

    def __str__(self):
        target = self.interface or self.device
        return f"{target} {self.metric}={self.value}" if target else self.metric


class Alert(models.Model):
    """Alert triggered when a metric threshold is crossed."""

    device = models.ForeignKey(
        Device, related_name="alerts", on_delete=models.CASCADE
    )
    metric = models.CharField(max_length=100)
    value = models.FloatField()
    threshold = models.FloatField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    cleared_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["device", "timestamp"])]

    def __str__(self):
        return f"{self.device} {self.metric}={self.value}"
