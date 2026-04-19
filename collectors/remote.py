import json
import os
import paramiko


def get_ssh_client(config: dict) -> paramiko.SSHClient:
    target = config["target"]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        key_path = target.get("key_path")
        if key_path:
            key_path = os.path.expanduser(key_path)
        client.connect(
            hostname=target["host"],
            port=target.get("port", 22),
            username=target["user"],
            key_filename=key_path,
            password=target.get("password")
        )
    except Exception as e:
        raise RuntimeError(f"Connexion SSH impossible à {target['host']} : {e}")
    return client


def run_command(client: paramiko.SSHClient, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode().strip() or stderr.read().decode().strip()


def get_snapshot(config: dict) -> dict:
    client = get_ssh_client(config)
    host = config["target"]["host"]
    hostname = run_command(client, "hostname")

    cpu    = run_command(client, "awk '/cpu / {u=$2+$4; t=$2+$3+$4+$5; printf \"%.1f\", u/t*100}' /proc/stat")
    ram    = run_command(client, "free -m | awk 'NR==2{printf \"{\\\"used\\\":%s,\\\"total\\\":%s}\", $3, $2}'")
    disk   = run_command(client, "df -h --output=target,size,used,pcent | tail -n +2")
    procs  = run_command(client, "ps aux --sort=-%cpu | head -6 | tail -5")
    uptime = run_command(client, "uptime -p")

    client.close()

    ram_data = json.loads(ram) if ram.startswith("{") else {"used": 0, "total": 0}

    return {
        "host": hostname or host,
        "platform": "Linux",
        "cpu": {"percent": float(cpu) if cpu else 0},
        "ram": {
            "used_gb": round(ram_data["used"] / 1024, 1),
            "total_gb": round(ram_data["total"] / 1024, 1),
            "percent": round(ram_data["used"] / ram_data["total"] * 100, 1) if ram_data["total"] else 0
        },
        "disk": disk,
        "top_processes": procs,
        "uptime": uptime
    }


def get_containers(config: dict) -> list[dict]:
    if not config["target"].get("docker"):
        return []
    client = get_ssh_client(config)
    output = run_command(
        client,
        "docker ps -a --format '{{.Names}}|{{.Status}}|{{.Image}}'"
    )
    client.close()

    containers = []
    for line in output.splitlines():
        if "|" in line:
            name, status, image = line.split("|", 2)
            containers.append({"name": name, "status": status, "image": image})
    return containers