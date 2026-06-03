#!/usr/bin/env python3
"""Rook — System-aware AI terminal copilot."""

__version__ = "0.1.0"

import argparse
import datetime
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOK_DIR = Path.home() / ".rook"
CONFIG_PATH = ROOK_DIR / "config.json"
CONTEXT_PATH = ROOK_DIR / "context.json"
INJECT_PIPE = ROOK_DIR / "inject.pipe"


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def load_context():
    if CONTEXT_PATH.exists():
        with open(CONTEXT_PATH) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# System Scanner
# ---------------------------------------------------------------------------

def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _get_disk():
    usage = shutil.disk_usage("/")
    fmt = lambda b: f"{b // (1 << 30)}G"
    return {"total": fmt(usage.total), "used": fmt(usage.used), "free": fmt(usage.free)}


def _get_cpu():
    try:
        import psutil
        return psutil.cpu_info().brand_raw
    except Exception:
        return _run("cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2").strip() or "unknown"


def _get_ram():
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1 << 30))
    except Exception:
        return 0


def _get_packages():
    pkgs = {}
    # apt
    apt_list = _run("dpkg --get-selections 2>/dev/null | grep -v deinstall | awk '{print $1}'")
    if apt_list:
        pkgs["apt"] = apt_list.splitlines()[:50]
    # pip
    pip_list = _run("pip3 list --format=columns 2>/dev/null | tail -n+3 | awk '{print $1}'")
    if pip_list:
        pkgs["pip"] = pip_list.splitlines()[:50]
    # npm
    npm_list = _run("npm list -g --depth=0 2>/dev/null | tail -n+2 | sed 's/.*── //' | sed 's/@.*//'")
    if npm_list:
        pkgs["npm"] = npm_list.splitlines()[:30]
    # cargo
    cargo_list = _run("ls ~/.cargo/bin/ 2>/dev/null")
    if cargo_list:
        pkgs["cargo"] = cargo_list.splitlines()[:30]
    return pkgs


def _get_services():
    running = _run("systemctl list-units --type=service --state=running --no-legend --no-pager 2>/dev/null | awk '{print $1}' | sed 's/.service$//'")
    available = _run("systemctl list-unit-files --type=service --no-legend --no-pager 2>/dev/null | awk '{print $1}' | sed 's/.service$//'")
    return {
        "running": running.splitlines()[:20] if running else [],
        "available": available.splitlines()[:30] if available else [],
    }


def _get_home_structure():
    structure = {}
    home = Path.home()
    for item in sorted(home.iterdir()):
        if item.name.startswith(".") or item.name in ("__pycache__", "node_modules"):
            continue
        if item.is_dir():
            try:
                subs = [s.name for s in sorted(item.iterdir()) if not s.name.startswith(".")][:10]
                structure[f"~/{item.name}"] = subs
            except PermissionError:
                structure[f"~/{item.name}"] = ["<permission denied>"]
    return structure


def _get_dotfiles():
    dots = {}
    home = Path.home()
    for name in (".zshrc", ".bashrc", ".gitconfig", ".env", ".vimrc", ".tmux.conf"):
        p = home / name
        if p.exists():
            try:
                content = p.read_text()[:2000]
                dots[name] = content
            except Exception:
                dots[name] = "<unreadable>"
    return dots


def _get_git_repos():
    repos = []
    home = Path.home()
    for d in home.rglob(".git"):
        repo = d.parent
        if repo == home or any(p.startswith(".") for p in repo.relative_to(home).parts):
            continue
        remote = _run(f"git -C '{repo}' remote get-url origin 2>/dev/null")
        branch = _run(f"git -C '{repo}' branch --show-current 2>/dev/null")
        repos.append({"path": str(repo), "remote": remote, "branch": branch})
        if len(repos) >= 20:
            break
    return repos


def _get_python_venvs():
    venvs = []
    home = Path.home()
    for venv in home.rglob("pyvenv.cfg"):
        venvs.append(str(venv.parent))
        if len(venvs) >= 10:
            break
    return venvs


def _get_docker_images():
    imgs = _run("docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null")
    return imgs.splitlines()[:20] if imgs else []


def _get_path_binaries():
    path = os.environ.get("PATH", "")
    bins = []
    for d in path.split(":"):
        dp = Path(d)
        if dp.is_dir():
            for f in list(dp.iterdir())[:5]:
                if f.is_file() and os.access(f, os.X_OK):
                    bins.append(str(f))
                    if len(bins) >= 30:
                        return bins
    return bins


def scan_system():
    print("▸ Scanning system...")
    ctx = {
        "os": f"{_run('lsb_release -d 2>/dev/null | cut -f2') or platform.platform()}",
        "kernel": platform.release(),
        "shell": os.environ.get("SHELL", "unknown"),
        "user": os.environ.get("USER", "unknown"),
        "home": str(Path.home()),
        "hostname": socket.gethostname(),
        "cpu": _get_cpu(),
        "ram_gb": _get_ram(),
        "disk": _get_disk(),
        "package_managers": [pm for pm in ["apt", "pip", "npm", "cargo"] if shutil.which(pm)],
        "installed_packages": _get_packages(),
        "path_binaries": _get_path_binaries(),
        "home_structure": _get_home_structure(),
        "dotfiles": _get_dotfiles(),
        "services": _get_services(),
        "env_vars": [k for k in os.environ.keys() if not k.startswith("_")][:30],
        "python_venvs": _get_python_venvs(),
        "docker_images": _get_docker_images(),
        "git_repos": _get_git_repos(),
        "last_scanned": datetime.datetime.now().isoformat(),
    }
    with open(CONTEXT_PATH, "w") as f:
        json.dump(ctx, f, indent=2)
    print(f"▸ System context saved to {CONTEXT_PATH}")
    return ctx


# ---------------------------------------------------------------------------
# AI Backend
# ---------------------------------------------------------------------------

WEB_KEYWORDS = re.compile(
    r"\b(latest|version|install|docs?|documentation|how to|error:|update|upgrade|release)\b",
    re.IGNORECASE,
)


def web_search(query, num_results=3):
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=num_results, advanced=True):
            results.append({"title": getattr(url, "title", ""), "url": getattr(url, "url", str(url)), "description": getattr(url, "description", "")})
        return results
    except Exception:
        return []


def build_system_prompt(context, history_lines):
    # Build compact context for small models
    if context:
        compact = {
            "os": context.get("os", ""),
            "kernel": context.get("kernel", ""),
            "shell": context.get("shell", ""),
            "user": context.get("user", ""),
            "hostname": context.get("hostname", ""),
            "cpu": context.get("cpu", ""),
            "ram_gb": context.get("ram_gb", ""),
            "disk": context.get("disk", {}),
            "package_managers": context.get("package_managers", []),
        }
        # Add top-level home structure only
        home = context.get("home_structure", {})
        compact["projects"] = list(home.keys())[:10]
        ctx_str = json.dumps(compact, indent=1)
    else:
        ctx_str = "No system context available. Run: rook scan"
    return f"""You are Rook, a terminal copilot running locally on this Linux machine.

You are a helpful friend who knows Linux. You see the user's system info, recent commands, and terminal output. You help them debug errors, find files, manage services, write scripts, and understand what's happening on their machine.

How to respond:
- Keep it short and conversational. One or two sentences unless they ask for detail.
- When suggesting a command, wrap it in <cmd>...</cmd> so it can be executed.
- If something is not installed, just say "install it" and give the command.
- Never invent file paths, flags, or package names. If unsure, say so.
- Plain text only. No markdown, no code fences, no asterisks, no headers.
- If asked who you are, say: "I'm Rook, your terminal copilot."
- You are NOT Cipher. You are NOT a generic AI assistant. You are Rook.

System info: {ctx_str}"""



def parse_response(text):
    # Strip markdown code fences
    text = re.sub(r"```[a-z]*\n?", "", text)
    text = re.sub(r"```", "", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def call_ai(messages, cfg):
    import requests
    model = cfg.get("model", "gemma3:1b")
    base_url = cfg.get("ollama_url", "http://localhost:11434")
    api_url = f"{base_url}/v1/chat/completions"
    resp = requests.post(
        api_url,
        headers={"Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 512},
        timeout=120,
    )
    if resp.status_code != 200:
        return f"API error {resp.status_code}: {resp.text[:200]}"
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def ai_query(user_input, mode="query"):
    cfg = load_config()
    context = load_context()

    sys_prompt = build_system_prompt(context, [])

    # Web search if needed
    web_context = ""
    if cfg.get("web_search", True) and WEB_KEYWORDS.search(user_input):
        results = web_search(user_input)
        if results:
            web_context = "\n\nWEB SEARCH RESULTS:\n" + "\n".join(
                f"- {r['title']}: {r['description'][:200]}" for r in results
            )

    if mode == "error":
        user_msg = f"The user ran a command that failed. Diagnose the error and suggest a fix.\n\n{user_input}"
    elif mode == "chat":
        user_msg = user_input
    else:
        user_msg = user_input

    if web_context:
        user_msg += web_context

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_msg},
    ]

    response = call_ai(messages, cfg)
    response = parse_response(response)

    return response


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def cmd_query(args):
    query = " ".join(args.query) if isinstance(args.query, list) else args.query
    resp = ai_query(query, mode="query")
    print(resp)


def cmd_error(args):
    payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    if not payload:
        print("Error: no payload on stdin. Expected JSON with command, exit_code, stderr.")
        sys.exit(1)
    prompt = f"Command: {payload.get('command', '?')}\nExit code: {payload.get('exit_code', '?')}\nStderr:\n{payload.get('stderr', '')}"
    resp = ai_query(prompt, mode="error")
    print(resp)


def cmd_scan(args):
    scan_system()


def cmd_status(args):
    cfg = load_config()
    ctx = load_context()
    recording = (ROOK_DIR / "recording.log").exists()
    print(f"  Version: {__version__}")
    print(f"  Model: {cfg.get('model', 'gemma3:1b')}")
    print(f"  Ollama URL: {cfg.get('ollama_url', 'http://localhost:11434')}")
    print(f"  Context: {'loaded' if ctx else 'not scanned yet'}")
    if ctx.get("last_scanned"):
        print(f"  Last scan: {ctx['last_scanned']}")
    print(f"  Terminal recording: {'active' if recording else 'not active'}")


def cmd_config(args):
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(CONFIG_PATH)])


def cmd_update(args):
    print("▸ Update requires git clone from the repository.")
    print("  Run: git clone <repo-url> /tmp/rook && bash /tmp/rook/install.sh")


def load_recording(max_lines=100):
    """Read the terminal recording file and return cleaned-up context."""
    recording_path = ROOK_DIR / "recording.log"
    if not recording_path.exists():
        return ""
    try:
        text = recording_path.read_text(errors="replace")
    except Exception:
        return ""
    # Strip ANSI escape codes
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    # Strip script headers/footers
    text = re.sub(r"Script started[^\n]*\n", "", text)
    text = re.sub(r"Script done[^\n]*\n?", "", text)
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Filter out known startup banner lines that would pollute the AI's context
    noise_patterns = [
        r"^=+\s*$",                              # ============ dividers
        r"^\s*I am Cipher\s*$",                  # Cipher banner
        r"^\s*Disciplined\s*\|.*$",              # Cipher tagline
        r"^\s*Build\.\s*Learn\..*$",             # Cipher tagline
        r"^\s*Focused\s*\|.*$",                  # Cipher tagline
        r"^\s*Relentless\s*\|.*$",               # Cipher tagline
    ]
    for pat in noise_patterns:
        text = re.sub(pat, "", text, flags=re.MULTILINE)
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines[-max_lines:])


def _rotate_recordings():
    """Truncate the recording files so a new chat starts with a clean slate.

    The parent's recording may contain startup banners, .zshrc content,
    or other noise from the previous shell session. We don't want that
    polluting the AI's understanding of what the user is doing.
    """
    for fname in ("recording.log", "terminal.log"):
        p = ROOK_DIR / fname
        if p.exists():
            try:
                p.write_text("")
            except Exception:
                pass


def load_cmd_log(max_lines=30):
    """Read the structured command log (timestamp|exit_code|command)."""
    log_path = ROOK_DIR / "terminal.log"
    if not log_path.exists():
        return ""
    try:
        lines = log_path.read_text().strip().splitlines()
    except Exception:
        return ""
    recent = lines[-max_lines:]
    parsed = []
    for line in recent:
        parts = line.split("|", 2)
        if len(parts) == 3:
            try:
                ts = int(parts[0])
                dt = datetime.datetime.fromtimestamp(ts)
                parsed.append(f"  {dt.strftime('%H:%M:%S')} [{parts[1]}] {parts[2]}")
            except (ValueError, OSError):
                parsed.append(f"  {line}")
    return "\n".join(parsed)


def print_banner():
    """Print the Rook startup banner."""
    g = chr(27) + "[1;32m"  # bold green
    d = chr(27) + "[0;90m"  # dim gray
    r = chr(27) + "[0m"     # reset

    print(
        f"\n{g}Rook v{__version__}{r}  {d}System-aware AI copilot{r}"
        f"\n{d}Type 'exit' or Ctrl+D to quit{r}\n"
    )


def cmd_chat(args):
    cfg = load_config()
    context = load_context()
    sys_prompt = build_system_prompt(context, [])
    messages = [{"role": "system", "content": sys_prompt}]

    # Rotate the terminal recordings so the chat REPL doesn't see the
    # user's previous shell session (which may include startup banners,
    # .zshrc content, or other noise). The new chat shell is clean; we
    # only want context from the rook session itself.
    _rotate_recordings()

    # Build terminal context
    terminal_ctx = ""
    recording = load_recording(max_lines=100)
    cmd_log = load_cmd_log(max_lines=30)
    parts = []
    if cmd_log:
        parts.append(f"Recent commands (timestamp | exit_code | command):\n{cmd_log}")
    if recording:
        parts.append(f"Terminal output:\n{recording[:2000]}")
    terminal_ctx = "\n\n".join(parts)

    if terminal_ctx:
        messages.append({
            "role": "system",
            "content": f"Terminal context from the user's current session:\n{terminal_ctx}",
        })

    # Show startup banner
    print_banner()

    initial = " ".join(args.chat) if hasattr(args, "chat") and args.chat else ""
    if initial:
        messages.append({"role": "user", "content": initial})
        resp = call_ai(messages, cfg)
        resp = parse_response(resp)
        print(f"\033[1;32mRook:\033[0m {resp}\n")
        messages.append({"role": "assistant", "content": resp})
    else:
        # Auto-greeting when chat opens without an initial message
        greeting = "Hello! I'm Rook, your terminal copilot. What can I help you with?"
        print(f"\033[1;32mRook:\033[0m {greeting}\n")
        messages.append({"role": "assistant", "content": greeting})

    while True:
        try:
            user = input("\033[1;36myou ▸ \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not user:
            continue
        if user.lower() in ("exit", "quit", "q"):
            print("Bye.")
            break
        messages.append({"role": "user", "content": user})
        resp = call_ai(messages, cfg)
        resp = parse_response(resp)
        print(f"\033[1;32mRook:\033[0m {resp}\n")
        messages.append({"role": "assistant", "content": resp})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="rook", description="Rook — System-aware AI terminal copilot")
    sub = parser.add_subparsers(dest="command")

    p_query = sub.add_parser("query")
    p_query.add_argument("query", nargs="+")

    p_chat = sub.add_parser("chat")
    p_chat.add_argument("chat", nargs="*", default=[])

    p_error = sub.add_parser("error")

    sub.add_parser("scan")
    sub.add_parser("status")
    sub.add_parser("config")
    sub.add_parser("update")

    args, unknown = parser.parse_known_args()

    if args.command == "query":
        cmd_query(args)
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "error":
        cmd_error(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "update":
        cmd_update(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
