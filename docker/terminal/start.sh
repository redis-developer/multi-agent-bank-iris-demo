#!/bin/bash
# Terminal panel: one tmux session per workbench terminal tab, each served
# by its own ttyd instance. Adapted from redislabs-training/btc-rag-chatbot.
set -euo pipefail

TMUX_CONFIG="${TMUX_CONFIG:-/etc/tmux.conf}"
TERMINAL_DIR="${TERMINAL_DIR:-/workshop}"
TERMINAL_SESSION_PREFIX="${TERMINAL_SESSION_PREFIX:-terminal}"
MAX_TERMINAL_SESSIONS="${MAX_TERMINAL_SESSIONS:-4}"
TERMINAL_PROMPT="${TERMINAL_PROMPT:-workshop:\\w\\$ }"
TTYD_BASE_PORT="${TTYD_BASE_PORT:-7681}"

tmux_has_session() {
  tmux -f "$TMUX_CONFIG" has-session -t "$1" 2>/dev/null
}

terminal_shell_command() {
  printf "PS1='%s' exec bash --noprofile --norc -i" "$TERMINAL_PROMPT"
}

start_ttyd_session() {
  local session_name="$1"
  local port="$2"

  if ! tmux_has_session "$session_name"; then
    tmux -f "$TMUX_CONFIG" new-session -d -s "$session_name" -c "$TERMINAL_DIR" "$(terminal_shell_command)"
    tmux -f "$TMUX_CONFIG" send-keys -t "$session_name" "clear" Enter
  fi

  TERMINAL_SESSION_NAME="$session_name" ttyd -W -p "$port" bash -lc '
    tmux_has_session() {
      tmux -f "$TMUX_CONFIG" has-session -t "$1" 2>/dev/null
    }

    terminal_shell_command() {
      printf "PS1='\''%s'\'' exec bash --noprofile --norc -i" "$TERMINAL_PROMPT"
    }

    if ! tmux_has_session "$TERMINAL_SESSION_NAME"; then
      tmux -f "$TMUX_CONFIG" new-session -d -s "$TERMINAL_SESSION_NAME" -c "$TERMINAL_DIR" "$(terminal_shell_command)"
      tmux -f "$TMUX_CONFIG" send-keys -t "$TERMINAL_SESSION_NAME" "clear" Enter
    fi

    exec tmux -f "$TMUX_CONFIG" attach-session -t "$TERMINAL_SESSION_NAME"
  ' &
}

export TMUX_CONFIG TERMINAL_DIR TERMINAL_PROMPT

for ((terminal_index = 0; terminal_index < MAX_TERMINAL_SESSIONS; terminal_index++)); do
  start_ttyd_session "${TERMINAL_SESSION_PREFIX}-${terminal_index}" $((TTYD_BASE_PORT + terminal_index))
done

wait -n
