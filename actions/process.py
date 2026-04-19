from collectors.remote import get_ssh_client, run_command


def kill_process(pid: int, sig: str = "SIGTERM", config: dict = None) -> str:
    client = get_ssh_client(config)
    result = run_command(client, f"kill -{sig} {pid}")
    client.close()
    return f"Signal {sig} envoyé au PID {pid}." if not result else result


def get_process_info(pid: int = None, name: str = None, config: dict = None) -> str:
    client = get_ssh_client(config)
    if pid:
        result = run_command(client, f"ps -p {pid} -o pid,comm,stat,pcpu,rss,args --no-headers")
    elif name:
        result = run_command(client, f"pgrep -a {name} | head -5")
    else:
        return "Fournir pid ou name."
    client.close()
    return result or "Processus introuvable."
