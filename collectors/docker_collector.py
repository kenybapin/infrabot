def get_containers() -> list[dict]:
    """Returns the state of Docker containers (if Docker is available)."""
    try:
        import docker
        client = docker.from_env()
        containers = []
        for c in client.containers.list(all=True):
            stats = c.stats(stream=False) if c.status == "running" else {}
            containers.append({
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "cpu_percent": _calc_cpu(stats) if stats else 0,
            })
        return containers
    except Exception:
        return [] # Docker not available or not started


def _calc_cpu(stats: dict) -> float:
    try:
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                    stats["precpu_stats"]["cpu_usage"]["total_usage"]
        sys_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                    stats["precpu_stats"]["system_cpu_usage"]
        return round((cpu_delta / sys_delta) * 100, 1) if sys_delta > 0 else 0.0
    except (KeyError, ZeroDivisionError):
        return 0.0