import subprocess


def restart_service(service: str) -> str:
    """Restarts a service via systemctl."""
    result = subprocess.run(
        ["systemctl", "restart", service],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return f"Service '{service}' restarted successfully."
    return f"Failed to restart '{service}': {result.stderr.strip()}"


def list_services() -> str:
    """List active systemd services."""
    result = subprocess.run(
        ["systemctl", "list-units", "--type=service", "--state=active", "--no-pager"],
        capture_output=True, text=True
    )
    return result.stdout