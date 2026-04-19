#!/usr/bin/env python3
"""
InfraBot — Agent IA DevOps local (Ollama + Linux/Docker)
Usage:
    python main.py              # Lance une analyse en dry-run
    python main.py --live       # Lance une analyse avec actions réelles
    python main.py --daemon     # Tourne en continu (interval depuis config.yaml)
    python main.py --history    # Affiche les dernières décisions
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
    table = Table(title="Dernières décisions InfraBot")
    table.add_column("Timestamp", style="dim")
    table.add_column("Outil")
    table.add_column("Résultat")
    table.add_column("Mode")

    for d in decisions:
        mode = "[yellow]dry-run[/yellow]" if d["dry_run"] else "[red]live[/red]"
        table.add_row(d["timestamp"][:19], d["tool"], d["result"][:60], mode)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="InfraBot — Agent IA DevOps local")
    parser.add_argument("--live", action="store_true", help="Mode live (actions réelles)")
    parser.add_argument("--daemon", action="store_true", help="Tourne en continu")
    parser.add_argument("--history", action="store_true", help="Affiche l'historique")
    parser.add_argument("--config", default="config.yaml", help="Chemin config")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.history:
        show_history()
        return

    dry_run = not args.live

    if dry_run:
        console.print("[yellow]Mode DRY-RUN activé — aucune action réelle[/yellow]")
    else:
        console.print("[red bold]Mode LIVE activé — les actions seront exécutées ![/red bold]")
        confirm = input("Confirmer ? (oui/non) : ")
        if confirm.lower() != "oui":
            console.print("Annulé.")
            return

    if args.daemon:
        interval_min = config["agent"]["interval_minutes"]
        interval_sec = interval_min * 60
        console.print(f"[blue]Mode daemon — analyse toutes les {interval_min} minutes[/blue]")
        while True:
            try:
                run_agent(config, dry_run=dry_run)
                console.print(f"\n[dim]Prochaine analyse dans {interval_min} min...[/dim]")
                time.sleep(interval_sec)
            except KeyboardInterrupt:
                console.print("\n[yellow]Daemon arrêté.[/yellow]")
                break
    else:
        run_agent(config, dry_run=dry_run)


if __name__ == "__main__":
    main()