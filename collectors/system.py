import psutil
import socket
import platform
from datetime import datetime


def get_snapshot() -> dict:
    """Collects the complete system status."""

    disk_usage = {}
    for partition in psutil.disk_partitions():
        if partition.fstype:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = {
                    "total_gb": round(usage.total / 1e9, 1),
                    "used_gb": round(usage.used / 1e9, 1),
                    "percent": usage.percent
                }
            except PermissionError:
                pass

    # Top 5 processes per CPU
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    top_processes = sorted(
        processes,
        key=lambda p: p.get("cpu_percent") or 0,
        reverse=True
    )[:5]

    return {
        "timestamp": datetime.now().isoformat(),
        "host": socket.gethostname(),
        "platform": platform.system(),
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(),
            "load_avg": list(psutil.getloadavg())
        },
        "ram": {
            "total_gb": round(psutil.virtual_memory().total / 1e9, 1),
            "used_gb": round(psutil.virtual_memory().used / 1e9, 1),
            "percent": psutil.virtual_memory().percent
        },
        "disk": disk_usage,
        "top_processes": top_processes,
        "network": {
            "bytes_sent_mb": round(psutil.net_io_counters().bytes_sent / 1e6, 1),
            "bytes_recv_mb": round(psutil.net_io_counters().bytes_recv / 1e6, 1)
        }
    }