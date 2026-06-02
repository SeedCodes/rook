#!/usr/bin/env bash
# Rook — Shell plugin for Bash and Zsh
# Source this file in your .bashrc or .zshrc

ROOK_DIR="$HOME/.rook"
ROOK_INJECT="$ROOK_DIR/inject.pipe"
ROOK_SUGGESTIONS="$ROOK_DIR/suggestions.log"
ROOK_ACTIVE=0
ROOK_INJECT_PID=""

# ---------------------------------------------------------------------------
# Command logging — captures every command with timestamp for terminal context
# ---------------------------------------------------------------------------

_rook_cmd_log() {
    local exit_code=$1
    if [ "$ROOK_ACTIVE" != "1" ]; then
        return
    fi
    local cmd_file="$ROOK_DIR/last_cmd.txt"
    if [ -f "$cmd_file" ]; then
        local cmd=$(cat "$cmd_file")
        rm -f "$cmd_file"
        echo "$(date +%s)|$exit_code|$cmd" >> "$ROOK_DIR/terminal.log"
    fi
}

# ---------------------------------------------------------------------------
# Inject pipe reader — runs in background, injects commands into shell buffer
# ---------------------------------------------------------------------------

_rook_inject_loop() {
    while true; do
        if [ -r "$ROOK_INJECT" ]; then
            cmd=$(head -1 "$ROOK_INJECT" 2>/dev/null)
            if [ -n "$cmd" ]; then
                tail -n +2 "$ROOK_INJECT" > "$ROOK_INJECT.tmp" 2>/dev/null && mv "$ROOK_INJECT.tmp" "$ROOK_INJECT" 2>/dev/null
                _rook_inject_cmd "$cmd"
            fi
        fi
        sleep 0.2
    done
}

_rook_inject_cmd() {
    local cmd="$1"
    if [ -n "$ZSH_VERSION" ]; then
        print -z "$cmd"
    elif [ -n "$BASH_VERSION" ]; then
        READLINE_LINE="$cmd"
        READLINE_POINT=${#cmd}
    fi
}

# ---------------------------------------------------------------------------
# Error hook — runs after every command, writes suggestion to file
# ---------------------------------------------------------------------------

_rook_error_hook() {
    local exit_code=$1
    if [ "$ROOK_ACTIVE" != "1" ]; then
        return
    fi
    if [ "$exit_code" -ne 0 ] && [ "$exit_code" -ne 130 ]; then
        local last_cmd=""
        if [ -n "$ZSH_VERSION" ]; then
            last_cmd=$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')
        else
            last_cmd=$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')
        fi
        # Save error info for rook chat to pick up
        echo "$last_cmd" > "$ROOK_DIR/last_error_cmd.txt"
        echo "$exit_code" > "$ROOK_DIR/last_error_code.txt"
        echo "Rook: run 'rook chat' for fix"
    fi
}

# ---------------------------------------------------------------------------
# Toggle on/off
# ---------------------------------------------------------------------------

rook_on() {
    ROOK_ACTIVE=1

    if [ ! -p "$ROOK_INJECT" ]; then
        mkfifo "$ROOK_INJECT" 2>/dev/null
    fi

    _rook_inject_loop &
    ROOK_INJECT_PID=$!

    if [ -n "$ZSH_VERSION" ]; then
        autoload -Uz add-zsh-hook 2>/dev/null

        if ! (( $+functions[_rook_precmd] )); then
            _rook_precmd() { _rook_cmd_log $?; _rook_error_hook $?; }
            add-zsh-hook precmd _rook_precmd 2>/dev/null || precmd_functions+=(_rook_precmd)
        fi

        if ! (( $+functions[_rook_preexec] )); then
            _rook_preexec() { echo "$1" > "$ROOK_DIR/last_cmd.txt"; }
            add-zsh-hook preexec _rook_preexec 2>/dev/null || preexec_functions+=(_rook_preexec)
        fi
    else
        if [[ "$PROMPT_COMMAND" != *"_rook_error_hook"* ]]; then
            PROMPT_COMMAND="_rook_error_hook \$?;${PROMPT_COMMAND}"
        fi
    fi

    # Start terminal recording via script (creates a subshell that is recorded)
    if [ -z "$ROOK_RECORDING_SESSION" ]; then
        touch "$ROOK_DIR/recording_active"
        export ROOK_RECORDING_SESSION=1
        echo "Rook recording started"
        script -q --flush -O "$ROOK_DIR/recording.log"
        rm -f "$ROOK_DIR/recording_active"
        echo "Rook recording stopped"
    fi

    echo "Rook is watching"
}

rook_off() {
    ROOK_ACTIVE=0

    if [ -n "$ROOK_INJECT_PID" ]; then
        kill "$ROOK_INJECT_PID" 2>/dev/null
        ROOK_INJECT_PID=""
    fi

    if [ -n "$ZSH_VERSION" ]; then
        precmd_functions=(${precmd_functions:#_rook_precmd})
        preexec_functions=(${preexec_functions:#_rook_preexec})
    else
        PROMPT_COMMAND="${PROMPT_COMMAND//_rook_error_hook;/}"
    fi

    rm -f "$ROOK_DIR/recording_active"
    rm -f "$ROOK_DIR/last_cmd.txt"
    rm -f "$ROOK_DIR/last_error_cmd.txt"
    rm -f "$ROOK_DIR/last_error_code.txt"

    echo "Rook offline"
}

# ---------------------------------------------------------------------------
# Main command dispatcher
# ---------------------------------------------------------------------------

rook() {
    case "${1:-}" in
        on)
            rook_on
            ;;
        off)
            rook_off
            ;;
        scan)
            python3 "$ROOK_DIR/rook.py" scan
            ;;
        query)
            shift
            if [ $# -gt 0 ]; then
                python3 "$ROOK_DIR/rook.py" query "$*"
            else
                echo "Usage: rook query <question>"
            fi
            ;;
        chat)
            # Check if there's a pending error to diagnose
            if [ -f "$ROOK_DIR/last_error_cmd.txt" ] && [ -f "$ROOK_DIR/last_error_code.txt" ]; then
                local err_cmd=$(cat "$ROOK_DIR/last_error_cmd.txt")
                local err_code=$(cat "$ROOK_DIR/last_error_code.txt")
                rm -f "$ROOK_DIR/last_error_cmd.txt" "$ROOK_DIR/last_error_code.txt"
                local payload="{\"command\": \"$err_cmd\", \"exit_code\": $err_code, \"stderr\": \"exit code $err_code\"}"
                echo "$payload" | python3 "$ROOK_DIR/rook.py" error
            else
                gnome-terminal --title "Rook Chat" -- python3 "$ROOK_DIR/rook.py" chat "$@"
            fi
            ;;
        config)
            python3 "$ROOK_DIR/rook.py" config
            ;;
        status)
            python3 "$ROOK_DIR/rook.py" status
            ;;
        update)
            python3 "$ROOK_DIR/rook.py" update
            ;;
        "")
            if [ "$ROOK_ACTIVE" = "1" ]; then
                rook_off
            else
                rook_on
            fi
            ;;
        *)
            if [[ "$1" == "??"* ]]; then
                local query="${1#??}"
                shift
                query="$query $*"
                query=$(echo "$query" | sed 's/^[[:space:]]*//')
                python3 "$ROOK_DIR/rook.py" query "$query"
            else
                echo "Usage: rook [on|off|scan|query|chat|config|status|update]"
                echo "  rook           — Toggle on/off"
                echo "  rook on        — Turn on + start recording"
                echo "  rook off       — Turn off"
                echo "  rook scan      — Re-scan system"
                echo "  rook query     — Ask a question"
                echo "  rook chat      — Open chat with terminal context"
                echo "  rook config    — Edit config"
                echo "  rook status    — Show status"
                echo "  rook update    — Update Rook"
            fi
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Zsh ZLE hook for ?? prefix
# ---------------------------------------------------------------------------

if [ -n "$ZSH_VERSION" ]; then
    _rook_zle_handler() {
        setopt LOCAL_OPTIONS NO_NOMATCH
        local cmd="$BUFFER"
        if [[ "$cmd" == "??"* ]]; then
            local query="${cmd#??}"
            query=$(echo "$query" | sed 's/^[[:space:]]*//')
            if [ -n "$query" ]; then
                local result=$(python3 "$ROOK_DIR/rook.py" query "$query" 2>/dev/null)
                BUFFER="$result"
                CURSOR=${#BUFFER}
                return
            fi
        fi
        zle .accept-line
    }
    zle -N _rook_zle_handler
    bindkey '^M' _rook_zle_handler 2>/dev/null
fi

# ---------------------------------------------------------------------------
# Auto-activation for recording sessions
# When rook on starts script, the inner shell sources this file.
# The recording_active flag tells us to auto-enable hooks.
# ---------------------------------------------------------------------------

if [ -f "$ROOK_DIR/recording_active" ]; then
    ROOK_ACTIVE=1

    if [ -n "$ZSH_VERSION" ]; then
        autoload -Uz add-zsh-hook 2>/dev/null

        # Set up precmd for command logging + error hook
        if ! (( $+functions[_rook_precmd] )); then
            _rook_precmd() { _rook_cmd_log $?; _rook_error_hook $?; }
            add-zsh-hook precmd _rook_precmd 2>/dev/null || precmd_functions+=(_rook_precmd)
        fi

        # Set up preexec for command capture
        if ! (( $+functions[_rook_preexec] )); then
            _rook_preexec() { echo "$1" > "$ROOK_DIR/last_cmd.txt"; }
            add-zsh-hook preexec _rook_preexec 2>/dev/null || preexec_functions+=(_rook_preexec)
        fi
    fi
fi

# Auto-create inject pipe on source
if [ ! -p "$ROOK_INJECT" ]; then
    mkfifo "$ROOK_INJECT" 2>/dev/null
fi
