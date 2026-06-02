# Contributing to Rook

Thanks for your interest in contributing! Rook is a small project and contributions of any size are welcome.

## Development Setup

1. **Fork and clone:**
   ```bash
   git clone https://github.com/SeedCodes/rook.git
   cd rook
   ```

2. **Install in development mode:**
   ```bash
   bash install.sh
   ```
   This copies files to `~/.rook/`. To test changes, copy them over manually:
   ```bash
   cp .rook/rook.py ~/.rook/rook.py
   cp .rook/rook.sh ~/.rook/rook.sh
   ```

3. **Run the test suite:**
   ```bash
   pip install -r requirements-dev.txt
   python -m pytest tests/
   ```

## Project Structure

```
Rook/
├── .rook/
│   ├── rook.py            # Python backend (AI, scanner, chat)
│   ├── rook.sh            # Shell plugin (hooks, recording)
│   ├── config.json        # Default config
│   └── requirements.txt   # Python dependencies
├── tests/                 # Pytest test suite
├── install.sh             # Installer
├── uninstall.sh           # Uninstaller
├── README.md
├── CHANGELOG.md
├── LICENSE
└── requirements-dev.txt   # Dev dependencies (pytest, etc.)
```

## Code Style

**Python** (`rook.py`):
- Follow PEP 8
- Use type hints for new functions
- Add docstrings to public functions
- Keep functions small and focused

**Shell** (`rook.sh`):
- Use 4-space indentation
- Quote all variables: `"$VAR"` not `$VAR`
- Prefer `[[ ]]` over `[ ]` in Bash
- Add comments for non-obvious logic

**Commit messages:**
- Use present tense: "Add feature" not "Added feature"
- Reference issues: "Fix #123: description"
- First line < 72 chars, blank line, then details

## Pull Request Process

1. **Create a branch:**
   ```bash
   git checkout -b feature/my-change
   ```

2. **Make your changes** and commit them.

3. **Run tests:**
   ```bash
   python -m pytest tests/
   bash -n .rook/rook.sh
   bash -n install.sh
   bash -n uninstall.sh
   ```

4. **Update CHANGELOG.md** under an "Unreleased" section.

5. **Push and open a PR** against the `main` branch.

6. **Describe the change** clearly in the PR description. Include:
   - What problem does it solve?
   - How did you test it?
   - Screenshots/recordings if UI-related

## Reporting Bugs

Open an issue on GitHub with:
- Rook version (`rook status`)
- OS and shell (`echo $OSTYPE; echo $SHELL`)
- Python version (`python3 --version`)
- Ollama version and model (`ollama --version; ollama list`)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs from `~/.rook/` (redact any sensitive info)

## Feature Requests

Open an issue with:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you considered

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Questions?

Open a discussion on GitHub or reach out in the issue tracker.
