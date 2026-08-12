#!/bin/sh
# Source non-empty values from the workshop .env before starting the
# Agent Memory Server, so a plain container restart picks up .env changes
# without recreation.
if [ -f /workshop-root/.env ]; then
  while IFS='=' read -r key value; do
    case "$key" in ''|\#*) continue ;; esac
    [ -n "$value" ] && export "$key=$value"
  done < /workshop-root/.env
fi
exec "$@"
