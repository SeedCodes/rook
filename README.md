# ⬛ Rook

> Your terminal, with memory. A context-aware AI copilot that knows your machine, your commands, and your mistakes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](#prerequisites)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-34%20passing-brightgreen.svg)](tests/)

---

## What can it do?

Rook turns your terminal into an AI-powered workbench. It **scans your entire system** on install, **watches everything you do**, and gives you an AI assistant that already knows your machine when you ask for help.

**It knows:**
- Your OS, kernel, CPU, RAM, disk
- Every package installed via apt/pip/npm/cargo
- All running services
- Your home directory structure
- Your dotfiles (`.zshrc`, `.gitconfig`, etc.)
- Every git repo you have
- All your Docker images
- Every command you've run (with exit codes)
- The full output of your last terminal session

**It can:**
- Diagnose failed commands in one shot
- Answer questions about your machine without you explaining it
- Suggest fixes that match your actual installed tools
- Continue a conversation with full context of what you tried
- Run completely offline via Ollama

---

## Demo

### Debug a failed command — Rook already saw it

```bash
$ docker run hello-world
docker: error during connect: cannot connect to daemon
$ rook chat
# → new terminal opens
you ▸ why did docker fail?
Rook: The Docker daemon isn't running. On this system (Ubuntu 26.04),
      start it with: sudo systemctl start docker
      Then add yourself to the docker group: sudo usermod -aG docker $USER
```

### Ask about your system — no setup needed

```bash
$ rook query "what's the best way to free up disk space on this machine?"
Rook: You have 380G free out of 500G, so disk isn't critical.
      Top space consumers I can see:
        - /var/log (~8G, mostly old journal files)
        - ~/.cache (3.2G, safe to clear)
        - Docker images: 12.4G total
      Try: sudo journalctl --vacuum-time=2w  and  docker system prune -a
```

### Multi-turn chat with full terminal context

```bash
$ rook on
$ cat /etc/nginx/sites-enabled/default
# ... see nginx config ...
$ nginx -t
nginx: [emerg] unknown directive "server_nam" in /etc/nginx/sites-enabled/default:42
$ rook chat
you ▸ what does that nginx error mean?
Rook: You have a typo on line 42 — "server_nam" should be "server_name".
      I can see your config has: server_nam example.com;
      Fix: change line 42 to read:  server_name example.com;

you ▸ also check for other typos
Rook: Looking at your config... line 47 has "listen 80 default_servr;" — 
      another typo, should be "default_server".
```

### Inline queries — no need to open a window

```bash
$ ?? find all python files modified in the last day
Rook: find . -name "*.py" -mtime -1 -type f

$ ?? how do I enable syntax highlighting in nano
Rook: Edit ~/.nanorc and add: include /usr/share/nano/*.nanorc
```

---

## Features

| Feature | Description |
|---------|-------------|
| **System scanner** | On install, captures OS, packages, services, projects, dotfiles, git repos, Docker images, venvs, PATH binaries |
| **Live terminal recording** | When `rook on` is active, every command + output is captured to `recording.log` via `script` |
| **Structured command log** | Every command logged with timestamp + exit code for precise error correlation |
| **Error diagnosis** | When a command fails, run `rook chat` — Rook already knows the error |
| **Local AI** | Powered by [Ollama](https://ollama.com) — no API keys, no cloud, fully private |
| **Multi-turn chat** | `rook chat` opens a new terminal with conversation memory |
| **Inline queries** | `?? your question` in any shell prompt for instant answers |
| **Web search** | Augments queries with current web results when needed (docs, latest versions) |
| **Shell hooks** | `preexec`/`precmd` capture everything without affecting your workflow |
| **Zero config** | Works out of the box with `gemma3:1b`; swap to `llama3.2:3b` for smarter responses |

---

## Quick Start

### Prerequisites

- **Linux** (Ubuntu, Fedora, Arch, etc.)
- **Python 3.8+**
- **`gnome-terminal`** — for the chat window
- **`script`** — from `util-linux` (preinstalled on most distros)
- **[Ollama](https://ollama.com/download)** — local AI runtime

### Install

```bash
git clone https://github.com/SeedCodes/rook.git
cd rook
bash install.sh
```

Restart your shell:
```bash
source ~/.zshrc   # or source ~/.bashrc
```

Pull a model and turn Rook on:
```bash
ollama pull gemma3:1b
rook on
```

That's it. Rook is now watching your terminal.

---

## Usage

| Command | Action |
|---------|--------|
| `rook` | Toggle on/off |
| `rook on` | Turn on + start recording |
| `rook off` | Turn off |
| `rook scan` | Re-scan system, rebuild context |
| `rook query <question>` | Ask a single question (one-shot) |
| `rook chat` | Open chat in a new terminal (multi-turn) |
| `?? <question>` | Inline query at any prompt |
| `rook config` | Edit config in `$EDITOR` |
| `rook status` | Show current state |
| `rook update` | Pull latest version |

---

## Real workflows

### 1. Diagnose anything instantly

```bash
$ apt install dockr
E: Unable to locate package dockr
$ rook chat
you ▸ I tried to install dockr
Rook: Typo — the package is "docker.io" on Debian/Ubuntu.
      Try: sudo apt install docker.io
```

### 2. Explore your own machine

```bash
$ rook query "what services are running on this system?"
$ rook query "show me my python virtual environments"
$ rook query "which docker images do I have and how big are they?"
$ rook query "what's the disk usage of my home directory?"
```

### 3. Learn while you work

```bash
$ curl -fsSL https://get.docker.com | sh
# ... 200 lines of output ...
$ rook query "explain what that docker install script just did"
```

### 4. Recover from mistakes

```bash
$ rm -rf ~/projects/important-thing
# oh no
$ rook chat
you ▸ I just deleted a project folder, can I recover it?
Rook: If the filesystem is ext4 and you act fast, you might be able to
      recover files using extundelete. Stop writing to the disk now.
      Install with: sudo apt install extundelete
      Then: sudo extundelete /dev/sdaX --restore-directory ~/projects
```

---

## Configuration

Edit `~/.rook/config.json`:

```json
{
  "model": "gemma3:1b",
  "ollama_url": "http://localhost:11434",
  "web_search": true,
  "theme": "dark",
  "scan_on_startup": false,
  "error_hook": true,
  "query_prefix": "??"
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `model` | `gemma3:1b` | Ollama model to use |
| `ollama_url` | `http://localhost:11434` | Ollama API endpoint |
| `web_search` | `true` | Augment queries with web search for current info |
| `query_prefix` | `??` | Inline query prefix |
| `error_hook` | `true` | Auto-capture failed commands |
| `scan_on_startup` | `false` | Re-scan on every shell start (slow) |

**Recommended models:**
- `gemma3:1b` — tiny (815MB), works everywhere, basic reasoning
- `llama3.2:3b` — better reasoning, 2GB
- `deepseek-coder:1.3b` — best for code questions, 776MB
- `llama3.2:1b` — alternative to gemma3, similar size

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│ Your terminal                                                │
│  ┌────────────────────────────────────┐                      │
│  │ You type commands                  │                      │
│  │   preexec → logs command string    │                      │
│  │   script   → records full output   │                      │
│  │   precmd  → logs exit code         │                      │
│  └────────────────┬───────────────────┘                      │
└───────────────────┼──────────────────────────────────────────┘
                    │  rook chat / rook query / ??
                    ▼
        ┌─────────────────────────────────┐
        │ rook.py                         │
        │   • Reads context.json          │
        │   • Reads terminal.log          │
        │   • Reads recording.log         │
        │   • Builds system prompt        │
        │   • Sends to Ollama (local)     │
        └────────────────┬────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Ollama          │
                │ (local AI)      │
                │ 127.0.0.1:11434 │
                └─────────────────┘
```

1. **System scan** — On install, Rook dumps your machine state to `~/.rook/context.json` (OS, packages, projects, dotfiles, etc.)
2. **Shell hooks** — `preexec` saves the command, `script` records output, `precmd` saves exit code — all in real time
3. **AI query** — When you ask, Rook assembles a system prompt with: system context + recent commands + terminal output
4. **Local inference** — Ollama runs the model locally. Nothing leaves your machine.

---

## Troubleshooting

**"ollama: command not found"**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:1b
```

**"gnome-terminal: command not found"**
```bash
sudo apt install gnome-terminal    # Ubuntu/Debian
sudo dnf install gnome-terminal    # Fedora
```

**Model gives poor responses**
Try a bigger model:
```bash
ollama pull llama3.2:3b
# then edit ~/.rook/config.json: "model": "llama3.2:3b"
```

**Chat window doesn't open**
Check that you're on X11 or Wayland with XWayland, and that `gnome-terminal` opens manually.

**"Rook recording stopped" appears unexpectedly**
The `script` session ended (you typed `exit` or the shell process exited). Run `rook on` again.

**Want to clear old recordings?**
```bash
rm ~/.rook/recording.log ~/.rook/terminal.log
```

---

## Uninstall

```bash
bash uninstall.sh
```

Removes `~/.rook/`, source lines from `.zshrc`/`.bashrc`, and stops all Rook processes.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE) © 2026 SeedCodes
