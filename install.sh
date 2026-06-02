#!/usr/bin/env bash
# Rook — Installer
# Creates ~/.rook/, installs deps, sources shell plugin

set -euo pipefail

ROOK_DIR="$HOME/.rook"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { printf "${GREEN}✓${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$1"; }
err()  { printf "${RED}✗${NC} %s\n" "$1" >&2; }

# ---------------------------------------------------------------------------
# OS check
# ---------------------------------------------------------------------------

if [[ "$OSTYPE" != "linux-gnu"* && "$OSTYPE" != "linux"* ]]; then
    err "Rook currently only supports Linux."
    err "Detected OS: $OSTYPE"
    exit 1
fi

# ---------------------------------------------------------------------------
# Prerequisite check
# ---------------------------------------------------------------------------

echo "▸ Checking prerequisites..."

missing=()

if ! command -v python3 >/dev/null 2>&1; then
    missing+=("python3 (Python 3.8+)")
fi

if ! command -v script >/dev/null 2>&1; then
    missing+=("util-linux (provides 'script')")
fi

if ! command -v gnome-terminal >/dev/null 2>&1; then
    missing+=("gnome-terminal (for rook chat window)")
fi

if ! command -v ollama >/dev/null 2>&1; then
    warn "Ollama not found. Install it from https://ollama.com/download"
    warn "Rook will install but chat won't work until Ollama is running."
fi

if [ ${#missing[@]} -ne 0 ]; then
    err "Missing required tools:"
    for tool in "${missing[@]}"; do
        err "  - $tool"
    done
    err "Install them and re-run this script."
    exit 1
fi

ok "All required tools found"

# ---------------------------------------------------------------------------
# Install files
# ---------------------------------------------------------------------------

echo "▸ Installing Rook to $ROOK_DIR..."

mkdir -p "$ROOK_DIR"

cp "$SCRIPT_DIR/.rook/config.json" "$ROOK_DIR/config.json" 2>/dev/null || true
cp "$SCRIPT_DIR/.rook/requirements.txt" "$ROOK_DIR/requirements.txt"
cp "$SCRIPT_DIR/.rook/rook.py" "$ROOK_DIR/rook.py"
cp "$SCRIPT_DIR/.rook/rook.sh" "$ROOK_DIR/rook.sh"
chmod +x "$ROOK_DIR/rook.py" "$ROOK_DIR/rook.sh"

ok "Files copied"

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------

echo "▸ Installing Python dependencies..."

if command -v pip3 >/dev/null 2>&1; then
    if pip3 install --user -r "$ROOK_DIR/requirements.txt" 2>/dev/null; then
        ok "Dependencies installed"
    elif pip3 install --break-system-packages -r "$ROOK_DIR/requirements.txt" 2>/dev/null; then
        ok "Dependencies installed"
    else
        warn "pip install failed. Run manually:"
        warn "  pip3 install --user -r $ROOK_DIR/requirements.txt"
    fi
else
    warn "pip3 not found. Install Python dependencies manually:"
    warn "  pip3 install --user -r $ROOK_DIR/requirements.txt"
fi

# ---------------------------------------------------------------------------
# Inject pipe
# ---------------------------------------------------------------------------

if [ ! -p "$ROOK_DIR/inject.pipe" ]; then
    mkfifo "$ROOK_DIR/inject.pipe" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Shell integration
# ---------------------------------------------------------------------------

SOURCE_LINE='[ -f ~/.rook/rook.sh ] && source ~/.rook/rook.sh'

add_to_rc() {
    local rc_file="$1"
    if [ -f "$rc_file" ]; then
        if grep -q "source ~/.rook/rook.sh\|\\.rook/rook.sh" "$rc_file" 2>/dev/null; then
            ok "$rc_file already has rook sourced"
        else
            printf "\n# Rook — AI terminal copilot\n%s\n" "$SOURCE_LINE" >> "$rc_file"
            ok "Added rook to $rc_file"
        fi
    fi
}

add_to_rc "$HOME/.bashrc"
add_to_rc "$HOME/.zshrc"

# ---------------------------------------------------------------------------
# Initial system scan
# ---------------------------------------------------------------------------

echo "▸ Running initial system scan..."

if python3 "$ROOK_DIR/rook.py" scan; then
    ok "System scan complete"
else
    warn "System scan failed. Run 'rook scan' manually later."
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo ""
printf "${GREEN}⬛ Rook installed successfully!${NC}\n"
echo ""
echo "  Restart your shell or run:  source ~/.zshrc"
echo "  Then type:                  rook on"
echo ""
echo "  Open chat anytime:          rook chat"
echo "  Ask a question:             rook query \"what's my shell?\""
echo ""
