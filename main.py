#!/usr/bin/env python3
"""
InfraBot — Local AI Agent (Ollama + Linux/Docker)
Usage:
    python main.py # Runs an analysis in dry-run
    python main.py --live # Runs an analysis with real actions
    python main.py --daemon # Runs continuously (interval from config.yaml)
    python main.py --history # Shows the latest decisions
"""

import argparse
import time
import yaml
from rich.console import Console
from rich.table import Table

from agent.loop import run_agent
from agent.memory import get_recent_decisions

console = Console()


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def show_history() -> None:
    decisions = get_recent_decisions(20)
    table = Table(title="Latest InfraBot decisions")
    table.add_column("Timestamp", style="dim")
    table.add_column("Tool")
    table.add_column("Result")
    table.add_column("Mode")

    for d in decisions:
        mode = "[yellow]dry-run[/yellow]" if d["dry_run"] else "[red]live[/red]"
        table.add_row(d["timestamp"][:19], d["tool"], d["result"][:60], mode)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="InfraBot — Agent IA local")
    parser.add_argument("--live", action="store_true", help="Live mode (real actions)")
    parser.add_argument("--daemon", action="store_true", help="Runs continuously")
    parser.add_argument("--history", action="store_true", help="Shows history")
    parser.add_argument("--config", default="config.yaml", help="Config path")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.history:
        show_history()
        return

    dry_run = not args.live

    if dry_run:
        console.print("[yellow]DRY-RUN mode activated — no real action[/yellow]")
    else:
        console.print("[red bold]LIVE mode activated — actions will be executed![/red bold]")
        confirm = input("Confirm ? (yes/no) : ")
        if confirm.lower() != "yes":
            console.print("Canceled.")
            return

    if args.daemon:
        interval_min = config["agent"]["interval_minutes"]
        interval_sec = interval_min * 60
        console.print(f"[blue]Daemon mode — scans all {interval_min} minutes[/blue]")
        while True:
            try:
                run_agent(config, dry_run=dry_run)
                console.print(f"\n[dim]Next analysis in {interval_min} min...[/dim]")
                time.sleep(interval_sec)
            except KeyboardInterrupt:
                console.print("\n[yellow]Daemon stopped.[/yellow]")
                break
    else:
        run_agent(config, dry_run=dry_run)


if __name__ == "__main__":
    main()
