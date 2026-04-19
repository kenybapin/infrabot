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


def execute_tool(name: str, args: dict, dry_run: bool) -> str:
    if name == "restart_service":
        if dry_run:
            return f"[DRY-RUN] Would have restarted the service: {args['service']}"
        return restart_service(args["service"])

    elif name == "kill_process":
        if dry_run:
            return f"[DRY-RUN] Would have killed the PID {args['pid']} with {args.get('signal', 'SIGTERM')}"
        return kill_process(args["pid"], args.get("signal", "SIGTERM"))

    elif name == "get_process_info":
        return get_process_info(args.get("pid"), args.get("name"))

    elif name == "check_disk":
        return _check_disk(args["path"])

    elif name == "list_large_files":
        return _list_large_files(args["path"], args.get("top_n", 10))

    elif name == "send_alert":
        return send_notification(args["message"], args.get("severity", "warning"))

    return f"Unknown tool: {name}"


def _check_disk(path: str) -> str:
    result = subprocess.run(["df", "-h", path], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


def _list_large_files(path: str, top_n: int) -> str:
    result = subprocess.run(
        ["du", "-sh", f"{path}/*"],
        capture_output=True, text=True, shell=False
    )
    lines = [l for l in result.stdout.strip().split("\n") if l]
    return "\n".join(lines[:top_n]) if lines else "No files found"

def _exec_in_container(container: str, command: str) -> str:
    from collectors.remote import get_ssh_client, run_command
    client = get_ssh_client(_config)
    result = run_command(client, f"docker exec {container} {command}")
    client.close()
    return result or "No exit."