import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from agent.client import get_ollama_client
from agent.tools import TOOLS, execute_tool
from agent.memory import save_decision
from collectors.remote import get_snapshot, get_containers


console = Console()

SYSTEM_PROMPT = """You are an expert Linux and Docker SRE.
You are provided with a system state snapshot of the machine {hostname}.

Your role:
1. Analyze the state and detect anomalies
2. Use available tools to diagnose and fix issues
3. Reason step-by-step (Reason → Act → Observe)
4. Be concise and precise in your decisions
5. Always mention the hostname of the analyzed machine in your conclusion

In dry-run mode, describe what you would do without executing.
In live mode, take action and explain what you did.

"""


def run_agent(config: dict, dry_run: bool = True) -> str:
    client, model = get_ollama_client(config)
    max_iter = config["agent"]["max_iterations"]

    console.print("[dim]Collecting system metrics...[/dim]")
    snapshot   = get_snapshot(config)
    containers = get_containers(config)

    context = {
        "snapshot": snapshot,
        "containers": containers,
        "mode": "DRY-RUN (no real action)" if dry_run else "LIVE (real action)"
    }

    mode_label = "[yellow]DRY-RUN[/yellow]" if dry_run else "[red]LIVE[/red]"
    host = snapshot["host"]
    cpu = snapshot["cpu"]["percent"]
    ram = snapshot["ram"]["percent"]
    console.print(Panel(
        f"Analysis started — mode {mode_label}\n"
        f"CPU: {cpu}% | RAM: {ram}% | Host: {host}",
        title="InfraBot",
        border_style="blue"
    ))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Current system status :\n{json.dumps(context, indent=2, ensure_ascii=False)}"}
    ]

    final_response = ""

    for iteration in range(max_iter):
        console.print(f"\n[dim]Iteration {iteration + 1}/{max_iter}...[/dim]")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            final_response = msg.content or ""
            console.print(Panel(final_response, title="Agent's conclusion", border_style="green"))
            break

        messages.append(msg)

        for call in msg.tool_calls:
            tool_name = call.function.name
            tool_args = json.loads(call.function.arguments)

            console.print(f"[cyan]Tool called :[/cyan] {tool_name}")
            console.print(Syntax(json.dumps(tool_args, indent=2), "json", theme="monokai"))

            result = execute_tool(tool_name, tool_args, dry_run)
            console.print(f"[green]Result :[/green] {result}")

            save_decision(config, {
                "tool": tool_name,
                "args": tool_args,
                "result": str(result),
                "dry_run": dry_run,
                "snapshot_cpu": cpu,
                "snapshot_ram": ram
            })

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result)
            })

    return final_response