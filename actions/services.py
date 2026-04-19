from collectors.remote import get_ssh_client, run_command


def restart_service(service: str, config: dict) -> str:
    client = get_ssh_client(config)
    result = run_command(client, f"systemctl restart {service}")
    client.close()
    return f"Service '{service}' redémarré." if not result else result


def list_services(config: dict) -> str:
    client = get_ssh_client(config)
    result = run_command(client, "systemctl list-units --type=service --state=active --no-pager")
    client.close()
    return result
