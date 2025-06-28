from pythonping import ping


def check_ping(host, count=1, timeout=1.0) -> bool:
    """Return True if host responds to ICMP ping."""
    try:
        response = ping(host, count=count, timeout=timeout)
        return response.success()
    except Exception:
        return False
