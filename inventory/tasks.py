from celery import shared_task
from .discovery import discover_network, periodic_scan
from django.utils import timezone
from .snmp import scan_device, discover_neighbors, gather_cam_arp, poll_metrics
from .ping import check_ping
from .models import Device, MetricRecord, Alert, AlertProfile


def _get_alert_profiles(device):
    """Return AlertProfiles linked to the device or its tags."""
    profiles = list(device.alert_profiles.all())
    tag_profiles = AlertProfile.objects.filter(tags__in=device.tags.all())
    for p in tag_profiles:
        if p not in profiles:
            profiles.append(p)
    return profiles


def _evaluate_alerts(device, metrics, timestamp):
    """Create or clear Alert objects based on metrics and profiles."""
    for profile in _get_alert_profiles(device):
        if profile.cpu_threshold is not None and metrics.get("cpu") is not None:
            value = metrics["cpu"]
            threshold = profile.cpu_threshold
            active = Alert.objects.filter(
                device=device, metric="cpu", cleared_at__isnull=True
            ).first()
            if value > threshold:
                if active:
                    active.value = value
                    active.threshold = threshold
                    active.save()
                else:
                    Alert.objects.create(
                        device=device,
                        metric="cpu",
                        value=value,
                        threshold=threshold,
                    )
            elif active:
                active.cleared_at = timestamp
                active.save()


@shared_task
def scan_device_task(ip, community="public"):
    """Scan a single device and return discovered host IPs."""
    device = scan_device(ip, community)
    if device is None:
        return []

    discover_neighbors(ip, community)
    gather_cam_arp(ip, community)

    from .models import Host

    return list(
        Host.objects.filter(interface__device=device).values_list("ip_address", flat=True)
    )


@shared_task
def discover_network_task(seed_ip, community="public"):
    """Celery task wrapper for discover_network."""
    return discover_network(seed_ip, community)


@shared_task
def periodic_scan_task(community="public"):
    """Rescan all known devices."""
    return periodic_scan(community)


@shared_task
def metric_poll_task(default_community="public"):
    """Poll devices for performance metrics and store results."""
    results = []
    timestamp = timezone.now()
    for device in Device.objects.all():
        if not device.management_ip:
            continue
        community = device.snmp_community or device.discovered_snmp_community or default_community
        metrics = poll_metrics(device.management_ip, community)

        if "cpu" in metrics:
            MetricRecord.objects.create(
                device=device,
                metric="cpu",
                value=metrics["cpu"],
                timestamp=timestamp,
            )
        if "memory" in metrics:
            MetricRecord.objects.create(
                device=device,
                metric="memory",
                value=metrics["memory"],
                timestamp=timestamp,
            )

        for iface_name, vals in metrics.get("interfaces", {}).items():
            iface = device.interfaces.filter(name=iface_name).first()
            if not iface:
                continue
            if vals.get("in_octets") is not None:
                MetricRecord.objects.create(
                    device=device,
                    interface=iface,
                    metric="in_octets",
                    value=vals["in_octets"],
                    timestamp=timestamp,
                )
            if vals.get("out_octets") is not None:
                MetricRecord.objects.create(
                    device=device,
                    interface=iface,
                    metric="out_octets",
                    value=vals["out_octets"],
                    timestamp=timestamp,
                )

        _evaluate_alerts(device, metrics, timestamp)
        results.append(device.management_ip)

    return results


@shared_task
def ping_check_task():
    """Ping all devices and record availability."""
    timestamp = timezone.now()
    results = []
    for device in Device.objects.all():
        if not device.management_ip:
            continue
        is_up = check_ping(device.management_ip)
        MetricRecord.objects.create(
            device=device,
            metric="ping",
            value=1 if is_up else 0,
            timestamp=timestamp,
        )
        device.is_online = is_up
        device.last_ping = timestamp
        device.save(update_fields=["is_online", "last_ping"])
        active = Alert.objects.filter(device=device, metric="ping", cleared_at__isnull=True).first()
        if not is_up:
            if not active:
                Alert.objects.create(device=device, metric="ping", value=0)
        elif active:
            active.value = 1
            active.cleared_at = timestamp
            active.save()
        results.append(device.management_ip)
    return results


@shared_task
def alert_check_task():
    """Evaluate recent metrics against alert profiles."""
    timestamp = timezone.now()
    for device in Device.objects.all():
        latest = {}
        for metric in ["cpu", "memory"]:
            rec = (
                device.metric_records.filter(metric=metric)
                .order_by("-timestamp")
                .first()
            )
            if rec:
                latest[metric] = rec.value
        _evaluate_alerts(device, latest, timestamp)
    return "alerts checked"
