import subprocess


def send_notification(message: str, severity: str = "warning") -> str:
    urgency = {"info": "low", "warning": "normal", "critical": "critical"}.get(severity, "normal")
    icons = {"info": "dialog-information", "warning": "dialog-warning", "critical": "dialog-error"}
    subprocess.run([
        "notify-send",
        "--urgency", urgency,
        "--icon", icons.get(severity, "dialog-warning"),
        f"InfraBot — {severity.upper()}",
        message
    ])
    return f"Notification sent: {message}"