import os
import signal
import psutil


def kill_process(pid: int, sig: str = "SIGTERM") -> str:
    signals = {
        "SIGTERM": signal.SIGTERM,
        "SIGKILL": signal.SIGKILL,
        "SIGHUP": signal.SIGHUP
    }
    try:
        os.kill(pid, signals.get(sig, signal.SIGTERM))
        return f"Signal {sig} envoyé au PID {pid}."
    except ProcessLookupError:
        return f"PID {pid} introuvable."
    except PermissionError:
        return f"Permission refusée pour le PID {pid}."


def get_process_info(pid: int = None, name: str = None) -> str:
    try:
        if pid:
            proc = psutil.Process(pid)
            info = {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(interval=0.5),
                "memory_mb": round(proc.memory_info().rss / 1e6, 1),
                "cmdline": " ".join(proc.cmdline())
            }
            return str(info)
        elif name:
            matches = [
                {"pid": p.pid, "name": p.name()}
                for p in psutil.process_iter(["pid", "name"])
                if name.lower() in p.info["name"].lower()
            ]
            return str(matches[:5])
    except psutil.NoSuchProcess:
        return "Processus introuvable."
    return "Fournir pid ou name."