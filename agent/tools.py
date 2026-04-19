import subprocess
import psutil
from actions.services import restart_service, list_services
from actions.process import kill_process, get_process_info
from actions.notify import send_notification


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "restart_service",
            "description": "Restarts a Linux systemd service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name (eg: nginx, postgresql, redis)"
                    }
                },
                "required": ["service"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process",
            "description": "Ends a process by its PID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid": {"type": "integer", "description": "Process PID"},
                    "signal": {
                        "type": "string",
                        "enum": ["SIGTERM", "SIGKILL", "SIGHUP"],
                        "default": "SIGTERM"
                    }
                },
                "required": ["pid"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_process_info",
            "description": "Gets details of a process by PID or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid": {"type": "integer"},
                    "name": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_disk",
            "description": "Checks the disk usage of a path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to parse (ex: /, /var)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_large_files",
            "description": "Lists the largest files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "top_n": {"type": "integer", "default": 10}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_alert",
            "description": "Sends a desktop notification via notify-send.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["info", "warning", "critical"],
                        "default": "warning"
                    }
                },
                "required": ["message"]
            }
        }
    }
]


def execute_tool(name: str, args: dict, dry_run: bool, config: dict) -> str:

    if name == "restart_service":
        if dry_run:
            return f"[DRY-RUN] Aurait redémarré le service : {args['service']}"
        return restart_service(args["service"], config)

    elif name == "kill_process":
        if dry_run:
            return f"[DRY-RUN] Aurait tué le PID {args['pid']} avec {args.get('signal', 'SIGTERM')}"
        return kill_process(args["pid"], args.get("signal", "SIGTERM"), config)

    elif name == "get_process_info":
        return get_process_info(args.get("pid"), args.get("name"), config)

    elif name == "check_disk":
        return _check_disk(args["path"], config)

    elif name == "list_large_files":
        return _list_large_files(args["path"], args.get("top_n", 10), config)

    elif name == "send_alert":
        return send_notification(args["message"], args.get("severity", "warning"))

    return f"Outil inconnu : {name}"


def _check_disk(path: str, config: dict) -> str:
    from collectors.remote import get_ssh_client, run_command
    client = get_ssh_client(config)
    result = run_command(client, f"df -h {path}")
    client.close()
    return result or f"Erreur sur {path}"


def _list_large_files(path: str, top_n: int, config: dict) -> str:
    from collectors.remote import get_ssh_client, run_command
    client = get_ssh_client(config)
    result = run_command(client, f"du -sh {path}/* 2>/dev/null | sort -rh | head -{top_n}")
    client.close()
    return result or "Aucun fichier trouvé"

def _exec_in_container(container: str, command: str) -> str:
    from collectors.remote import get_ssh_client, run_command
    client = get_ssh_client(_config)
    result = run_command(client, f"docker exec {container} {command}")
    client.close()
    return result or "No exit."
