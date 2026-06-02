#!/usr/bin/env bash
# Rook — Uninstaller
# Removes ~/.rook/ and cleans up shell rc files

set -euo pipefail

ROOK_DIR="$HOME/.rook"
SOURCE_PATTERN='\.rook/rook\.sh'
SOURCE_COMMENT='# Rook — AI terminal copilot'

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { printf "${GREEN}✓${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$1"; }
err()  { printf "${RED}✗${NC} %s\n" "$1" >&2; }

# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------

if [ ! -d "$ROOK_DIR" ] && ! grep -q "$SOURCE_PATTERN" "$HOME/.bashrc" "$HOME/.zshrc" 2>/dev/null; then
    warn "Rook is not installed."
    exit 0
fi

printf "${YELLOW}This will remove:${NC}\n"
echo "  - $ROOK_DIR (all data, recordings, context)"
echo "  - Source lines from ~/.bashrc and ~/.zshrc"
echo ""
read -r -p "Continue? [y/N] " response
case "$response" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "Cancelled."; exit 0 ;;
esac

# ---------------------------------------------------------------------------
# Kill any running Rook processes
# ---------------------------------------------------------------------------

echo "▸ Stopping Rook processes..."

pkill -f "rook.py" 2>/dev/null || true
pkill -f "script.*recording.log" 2>/dev/null || true
ok "Processes stopped"

# ---------------------------------------------------------------------------
# Remove source lines from shell rc files
# ---------------------------------------------------------------------------

remove_from_rc() {
    local rc_file="$1"
    if [ -f "$rc_file" ] && grep -q "$SOURCE_PATTERN" "$rc_file" 2>/dev/null; then
        # Remove Rook block (comment + source line + blank line)
        sed -i "/$SOURCE_COMMENT/,/$SOURCE_PATTERN/d" "$rc_file"
        ok "Removed rook from $rc_file"
    fi
}

echo "▸ Cleaning shell rc files..."
remove_from_rc "$HOME/.bashrc"
remove_from_rc "$HOME/.zshrc"

# ---------------------------------------------------------------------------
# Remove data directory
# ---------------------------------------------------------------------------

if [ -d "$ROOK_DIR" ]; then
    echo "▸ Removing $ROOK_DIR..."
    rm -rf "$ROOK_DIR"
    ok "Removed $ROOK_DIR"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

printf "\n${GREEN}⬛ Rook uninstalled successfully.${NC}\n"
echo "Restart your shell to apply changes."
