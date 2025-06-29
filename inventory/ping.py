from pythonping import ping
import subprocess
import os


def _system_ping(host: str, count: int, timeout: float) -> bool:
    """Fallback ping using system `ping` command."""
    cmd = ["ping", "-c", str(count), "-w", str(int(timeout)), host]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def check_ping(host, count=1, timeout=1.0) -> bool:
    """Return True if host responds to ICMP ping."""
    try:
        response = ping(host, count=count, timeout=timeout)
        return response.success()
    except PermissionError:
        # Raw socket requires root; fallback to system ping
        return _system_ping(host, count, timeout)
    except Exception:
        return _system_ping(host, count, timeout)
