#!/bin/sh
# Prepare the code-server data dir on every compose-up.
# - Fixes ownership so code-server (uid 1000) can write its state
# - Seeds a user-level settings.json that suppresses the welcome page,
#   the chat command center, telemetry, etc.
# Idempotent: safe to run on every boot.
set -e

DATA_DIR=/home/coder/.local/share/code-server
CODE_DIR=/home/coder/code
USER_DIR="$DATA_DIR/User"
EXTENSIONS_DIR="$DATA_DIR/extensions"
WORKSHOP_EXTENSION_SRC=/seed/extensions/workshop-open-file
WORKSHOP_EXTENSION_DEST="$EXTENSIONS_DIR/redis.workshop-open-file-0.0.1"
WORKSHOP_EXTENSION_ID=redis.workshop-open-file
WORKSHOP_EXTENSION_PROFILE="$EXTENSIONS_DIR/extensions.json"

mkdir -p "$USER_DIR" "$EXTENSIONS_DIR"
chown -R 1000:1000 "$DATA_DIR"

if [ -d "$CODE_DIR" ]; then
  chown -R 1000:1000 "$CODE_DIR"
  chmod -R u+rwX "$CODE_DIR"
fi

# Always (re)write the seed settings — the workshop owns these defaults.
cp /seed/settings.json "$USER_DIR/settings.json"
chown 1000:1000 "$USER_DIR/settings.json"

if [ -d "$WORKSHOP_EXTENSION_SRC" ]; then
  rm -rf "$WORKSHOP_EXTENSION_DEST"
  mkdir -p "$WORKSHOP_EXTENSION_DEST"
  cp -R "$WORKSHOP_EXTENSION_SRC"/. "$WORKSHOP_EXTENSION_DEST"/
  chown -R 1000:1000 "$WORKSHOP_EXTENSION_DEST"

  installed_timestamp="$(($(date +%s) * 1000))"
  workshop_extension_entry="{\"identifier\":{\"id\":\"$WORKSHOP_EXTENSION_ID\"},\"version\":\"0.0.1\",\"location\":{\"\$mid\":1,\"fsPath\":\"$WORKSHOP_EXTENSION_DEST\",\"external\":\"file://$WORKSHOP_EXTENSION_DEST\",\"path\":\"$WORKSHOP_EXTENSION_DEST\",\"scheme\":\"file\"},\"relativeLocation\":\"redis.workshop-open-file-0.0.1\",\"metadata\":{\"installedTimestamp\":$installed_timestamp,\"pinned\":true,\"source\":\"vsix\"}}"

  if [ ! -s "$WORKSHOP_EXTENSION_PROFILE" ]; then
    printf '[%s]\n' "$workshop_extension_entry" > "$WORKSHOP_EXTENSION_PROFILE"
  elif ! grep -q "\"id\":\"$WORKSHOP_EXTENSION_ID\"" "$WORKSHOP_EXTENSION_PROFILE"; then
    profile_content="$(tr -d '\n' < "$WORKSHOP_EXTENSION_PROFILE")"
    case "$profile_content" in
      "[]"|"[ ]")
        printf '[%s]\n' "$workshop_extension_entry" > "$WORKSHOP_EXTENSION_PROFILE"
        ;;
      *])
        printf '%s,%s]\n' "${profile_content%]}" "$workshop_extension_entry" > "$WORKSHOP_EXTENSION_PROFILE"
        ;;
      *)
        printf '[%s]\n' "$workshop_extension_entry" > "$WORKSHOP_EXTENSION_PROFILE"
        ;;
    esac
  fi

  if [ -f "$EXTENSIONS_DIR/.obsolete" ] && grep -q "$WORKSHOP_EXTENSION_ID" "$EXTENSIONS_DIR/.obsolete"; then
    rm -f "$EXTENSIONS_DIR/.obsolete"
  fi

  chown 1000:1000 "$WORKSHOP_EXTENSION_PROFILE"
fi

echo "vscode-init: prepared $DATA_DIR"
