import json
import sqlite3
import os
from datetime import datetime


def save_decision(config: dict, decision: dict) -> None:
    """Saves an agent decision (JSONL + SQLite)."""
    log_path = config["audit"]["log_path"]
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    entry = {"timestamp": datetime.now().isoformat(), **decision}

    with open(log_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    _save_to_sqlite(entry)


def _save_to_sqlite(entry: dict) -> None:
    conn = sqlite3.connect("audit/infrabot.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, tool TEXT, args TEXT,
            result TEXT, dry_run INTEGER,
            cpu_percent REAL, ram_percent REAL
        )
    """)
    conn.execute(
        "INSERT INTO decisions (timestamp, tool, args, result, dry_run, cpu_percent, ram_percent) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (entry.get("timestamp"), entry.get("tool"), json.dumps(entry.get("args", {})),
         entry.get("result"), int(entry.get("dry_run", True)),
         entry.get("snapshot_cpu"), entry.get("snapshot_ram"))
    )
    conn.commit()
    conn.close()


def get_recent_decisions(limit: int = 20) -> list[dict]:
    try:
        conn = sqlite3.connect("audit/infrabot.db")
        rows = conn.execute(
            "SELECT timestamp, tool, args, result, dry_run FROM decisions ORDER BY id DESC LIMIT?",
            (limit,)
        ).fetchall()
        conn.close()
        return [{"timestamp": r[0], "tool": r[1], "args": r[2], "result": r[3], "dry_run": bool(r[4])} for r in rows]
    except Exception:
        return[]