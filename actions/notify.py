import subprocess

def send_notification(message: str, severity: str = "warning") -> str:
    urgency = {"info": "low", "warning": "normal", "critical": "critical"}.get(severity, "normal")
    icons = {"info": "dialog-information", "warning": "dialog-warning", "critical": "dialog-error"}
    try:
        subprocess.run(
            [
                "notify-send",
                "--urgency", urgency,
                "--icon", icons.get(severity, "dialog-warning"),
                f"InfraBot — {severity.upper()}",
                message
            ],
            check=True
        )
        return f"Notification envoyée : {message}"
    except FileNotFoundError:
        return f"[notify-send indisponible] Alerte : {message}"
    except Exception as e:
        return f"Erreur notification : {e}"
