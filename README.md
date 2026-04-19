# InfraBot — Local AI Agent with Ollama
---

## Summary

1. [Introduction](#1-Introduction)
2. [Architecture](#2-architecture)
3. [Prerequisites & installation](#3-prerequisites--installation)
4. [Project structure](#4-project-structure)
5. [Configuration](#5-configuration)
6. [Code — collection layer](#6-code--collection-layer)
7. [Code — AI agent (ReAct loop)](#7-code--agent-ia-react-loop)
8. [Code — tools & actions](#8-code--tools--actions)
9. [Code — logging](#9-code--logging)
10. [Main entry point](#10-main-entry-point)
11. [Start project](#11-start-project)
12. [Go further](#12-go-further)

---

## 1. Introduction

**InfraBot** is an autonomous AI agent that monitors a Linux system or Docker containers, detects anomalies, reasons about the causes, and executes (or proposes) corrective actions.
It works entirely locally thanks to **Ollama**

### What the agent does

- Collects system state every N minutes (CPU, RAM, disk, proc...)
- Analysis via a local LLM (qwen2.5:14b) in loop **Reason → Act → Observe**
- Calls real tools: restart a service, kill a process, free disk
- Logs each decision in an append-only JSON file
- Send a desktop notification via `notify-send` (optional)


### Dry-run vs live mode

* dry-run → the agent analyzes and describes what it would do (no real action)
* live → the agent really executes the actions (to be activated consciously)


---

## 2. Architecture

```
1. COLLECTION: psutil · Docker SDK · df
2. AI AGENT: 
    - ReAct loop (Reason → Act → Observe)
    - LLM: Ollama qwen2.5:14b · SQLite memory
3. ACTIONS: systemctl · kill · Docker · notify-send
4. AUDIT decisions.jsonl · RichUI
```

---

## 3. Prerequisites & installation

### 3.1 Python 3.12

```bash
sudo apt install python3.12 python3.12-venv
python3 --version # Python 3.12.x
```

### 3.2 Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server in background
ollama serve &

# Download an run the recommended template
# qwen2.5:14b = best tool use local, ~9 GB RAM
# Check that the model responds
ollama run qwen2.5:14b "Just answer 'ok'"
```

> **Why qwen2.5:14b?**
> It is currently the best open-source model for function calling (tool use).
> It generates reliable structured JSON, an essential condition for the ReAct loop.

### 3.3 Docker (optional)

```bash
sudo apt install docker.io
sudo usermod -aG docker $USER
```

### 3.4 Create the Python project

```bash
mkdir infrabot && cd infrabot
python3 -m venv .venv
source .venv/bin/activate

pip install openai psutil docker rich pyyaml paramiko
```

---

## 4. Project structure

```
infrabot/
├── main.py # Entry point
├── config.yaml # Configuration (thresholds, model, mode)
├── agent/
│ ├── __init__.py
│ ├── client.py # Ollama connection
│ ├── loop.py # ReAct loop
│ ├── memory.py # SQLite history
│ └── tools.py # Defining and running tools
├── collectors/
│ ├── __init__.py
│ ├── system.py # psutil — CPU, RAM, disk, process
│ └── docker_collector.py # Docker Containers
├── actions/
│ ├── __init__.py
│ ├── services.py # Services management (systemctl)
│ ├── process.py # Kill / renice
│ └── notify.py # notify-send desktop
├── audit/
│ └── decisions.jsonl # Log append-only (automatically created)
└── README.md

Execution workflow : 
config.yaml → main.py → agent/client.py → collectors/remote.py → agent/loop.py → agent/tools.py → actions/services.py · actions/process.py · actions/notify.py → agent/memory.py → audit/decisions.jsonl
```

---

## 5. Target

Modify the `config.yaml` file to target the remote server to be monitored.
```yaml
target:
  host: "192.168.1.10"
  port: 22 
  user: "root"
  key_path: "~/.ssh/id_rsa"
  docker: false
```
Configure SSH access with your localhost `authorized_keys`, build and deploy the container in detached mode using  `Dockerfile` and `docker-compose.yml`.
```
cd infrabot/
cp ~/.ssh/id_rsa.pub ./authorized_keys
docker compose up -d --build

# Verify the deployment by connecting to the container
ssh -i ~/.ssh/id_rsa -p 2222 root@localhost
```


## 6. Start the project

```bash
#1. Check that Ollama is running
ollama serve &
ollama list # should display qwen2.5:14b

#2. Enable Python environment
cd infrabot
source .venv/bin/activate

# 3. First analysis in dry-run
python main.py

# Unique analysis — live (real actions)
python main.py --live

# Daemon mode — runs continuously
python main.py --daemon

# View decision history
python main.py --history
```

### Example of expected output

```
InfraBot
│ Analysis started — DRY-RUN mode
│ CPU: 12.4% | RAM: 67.2% | Host: web-01


Iteration 1/6...
Tool called: check_disk
{ "path": "/" }
Result: Filesystem Size Used Avail Use%
/dev/sda1 50G 18G 30G 37% /

Iteration 2/6...

Agent's conclusion 
│ Analysis completed. No critical anomalies
│ detected. CPU and RAM within thresholds.
│ Main disk at 37% — OK.
```

---

## 7. Go further

###  Simulate an incident in a container

```bash
# 1) Access the container
ssh -i ~/.ssh/id_rsa -p 2222 root@localhost
# 2) Inside the container, stress the CPU (1 core at 100%)
dd if=/dev/zero of=/dev/null
# 3) Run the Agent in dry-run from your local machine
python main.py
```
```
╭────────── Agent Conclusion ───────────────────────────────────╮
│ Analyzed machine: web-01                                      │
│                                                                │
│ Anomaly detected: process dd (PID 142) is consuming 98% CPU.   │
│ This is an infinite loop read/write command on /dev/null with  │
│ no productive utility.                                         │
│                                                                │
│ Recommended action: kill -SIGTERM 142                         │
│ In live mode, I would have executed: kill_process(pid=142)    │
╰────────────────────────────────────────────────────────────────╯
```

### Test the quality of the model

```bash
ollama run qwen2.5:14b << 'EOF'
You are a DevOps agent. Here are the tools available:
- restart_service(service: str)
- kill_process(pid: int)

CPU at 98%, nginx PID 1234 process consumes 95%.
What are you doing ? Respond with a JSON tool call.
EOF
```

---

## Resources

- [Ollama — models available](https://ollama.com/library)
- [psutil documentation](https://psutil.readthedocs.io)
- [OpenAI Python SDK (Ollama compatible)](https://github.com/openai/openai-python)
- [Rich — terminal UI](https://rich.readthedocs.io)
