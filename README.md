# ⬛ Rook

> System-aware AI terminal copilot for Linux. Watches your shell, understands your machine, and answers with context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](#prerequisites)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## What is Rook?

Rook is a shell plugin that turns your terminal into a context-aware AI assistant. It scans your system, watches what you do, and lets you ask questions or chat with a local AI model — all without leaving the terminal.

```
$ exho $SHELL
zsh: command not found: exho
$ rook chat
# → New terminal window opens with full context
Rook: You typed "exho" instead of "echo". Try: echo $SHELL
```

## Features

- **System context** — Scans OS, packages, services, projects, dotfiles on install
- **Live terminal recording** — When active, captures everything you do for richer AI responses
- **Error diagnosis** — Failed commands get auto-diagnosed with fixes
- **Local AI** — Uses Ollama (no API keys, no cloud, fully private)
- **In-line queries** — Type `?? your question` to ask without opening chat
- **Multi-turn chat** — `rook chat` opens a new terminal with a full REPL
- **Zero config** — Works out of the box with `gemma3:1b`

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

## Usage

| Command | Action |
|---------|--------|
| `rook` | Toggle on/off |
| `rook on` | Turn on + start recording |
| `rook off` | Turn off |
| `rook scan` | Re-scan system, rebuild context |
| `rook query <question>` | Ask a single question |
| `rook chat` | Open chat in a new terminal |
| `?? <question>` | In-line query (anywhere in your shell) |
| `rook config` | Edit config in `$EDITOR` |
| `rook status` | Show current state |
| `rook update` | Pull latest version |

### Examples

**Ask about your system:**
```bash
rook query "what shell am I using"
rook query "list my git repos"
rook query "what's taking up the most disk space"
```

**Diagnose errors automatically:**
```bash
$ exho $SHELL
zsh: command not found: exho
$ rook chat
# → Rook knows you meant "echo" and explains
```

**Chat in-line with context:**
```bash
$ rook on
$ docker ps
$ rook chat
# → New window opens, Rook sees your docker attempt
you ▸ why didn't docker ps work?
Rook: The docker daemon might not be running...
```

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
| `web_search` | `true` | Augment queries with web search |
| `query_prefix` | `??` | In-line query prefix |
| `error_hook` | `true` | Auto-diagnose failed commands |

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Your terminal                                          │
│  ┌──────────────────────────────────┐                  │
│  │ You type commands                │                  │
│  │  • preexec → logs command        │                  │
│  │  • script → records output       │                  │
│  │  • precmd → logs exit code       │                  │
│  └──────────────────────────────────┘                  │
└────────────────────┬────────────────────────────────────┘
                     │ rook chat
                     ▼
        ┌──────────────────────────┐
        │ New gnome-terminal       │
        │ with chat REPL           │
        │  • Reads recording.log   │
        │  • Reads terminal.log    │
        │  • Reads context.json    │
        │  • Sends to Ollama       │
        └──────────────────────────┘
```

1. **System scan** — On install, Rook builds `~/.rook/context.json` (OS, packages, projects, etc.)
2. **Shell hooks** — `preexec` and `precmd` log every command with timestamps and exit codes
3. **Terminal recording** — `script` utility captures the full terminal output to `recording.log`
4. **AI query** — When you run `rook query` or `rook chat`, the context is injected into the prompt
5. **Local inference** — Ollama runs the model locally, keeping everything private

## Troubleshooting

**"ollama: command not found"**
Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`

**"gnome-terminal: command not found"**
Install it: `sudo apt install gnome-terminal` (Ubuntu) or your distro's equivalent.

**Model gives poor responses**
Try a bigger model: `ollama pull llama3.2:3b` and update `config.json`.

**Chat window doesn't open**
Make sure `gnome-terminal` is installed and your `$DISPLAY` (X11) or Wayland session is running.

**"Rook recording stopped" appears unexpectedly**
The `script` session ended (you typed `exit` or the shell process exited). Run `rook on` again to restart.

## Uninstall

```bash
bash uninstall.sh
```

Removes `~/.rook/`, source lines from `.zshrc`/`.bashrc`, and stops all Rook processes.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE) © 2026 SeedCodes
