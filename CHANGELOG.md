# Changelog

All notable changes to Rook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-02

### Added
- Initial open source release
- System scanner — collects OS, packages, services, projects, dotfiles
- Local AI backend via [Ollama](https://ollama.com/) (no cloud, no API keys)
- Shell hooks (`preexec`/`precmd`) for command logging and error detection
- Terminal recording via `script` for full AI context
- `??` prefix for in-line queries
- `rook chat` opens a new terminal window with a multi-turn chat REPL
- `rook query` for single questions
- `rook scan` for rebuilding system context
- `rook config` for editing config in `$EDITOR`
- `rook status` for showing current state
- Web search augmentation (optional, via `googlesearch-python`)

### Components
- `rook.sh` — Shell plugin (273 lines, Bash + Zsh compatible)
- `rook.py` — Python backend (508 lines, Python 3.8+)
- `install.sh` — Installer with prerequisite checks
- `uninstall.sh` — Clean uninstaller

### Known Limitations
- Linux only (requires `gnome-terminal`)
- Small models like `gemma3:1b` may give poor reasoning — use `llama3.2:3b` or larger
- Recording stops when you `exit` the recorded session (run `rook on` again)

[0.1.0]: https://github.com/SeedCodes/rook/releases/tag/v0.1.0
