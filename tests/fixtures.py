"""Test fixtures: sample terminal recording and command log."""

SAMPLE_RECORDING = """Script started on 2026-06-02 18:30:00+05:30 [COMMAND="" <not executed on terminal>]
exho $SHELL
zsh: command not found: exho
echo $SHELL
/usr/bin/zsh
ls ~/Documents
test_file.txt
notes.md
Script done on 2026-06-02 18:31:00+05:30 [COMMAND_EXIT_CODE="0"]
"""

SAMPLE_RECORDING_WITH_ANSI = """\x1b[32mexho $SHELL\x1b[0m
zsh: command not found: exho
\x1b[1;36mecho $SHELL\x1b[0m
/usr/bin/zsh
Script done on 2026-06-02 18:31:00+05:30 [COMMAND_EXIT_CODE="0"]
"""

SAMPLE_TERMINAL_LOG = """1780405398|127|exho $SHELL
1780405450|0|echo $SHELL
1780405500|0|ls ~/Documents
"""

SAMPLE_CONTEXT = {
    "os": "Ubuntu 26.04 LTS",
    "kernel": "7.0.0-15-generic",
    "shell": "/usr/bin/zsh",
    "user": "simran",
    "hostname": "simran",
    "cpu": "AMD Ryzen 5",
    "ram_gb": 16,
    "disk": {"total": "500G", "used": "120G", "free": "380G"},
    "package_managers": ["apt", "pip", "npm"],
    "home_structure": {"~/Desktop": ["Rook"], "~/Documents": []},
}
