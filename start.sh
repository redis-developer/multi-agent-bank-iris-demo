#!/usr/bin/env bash
# One-command boot for the workshop.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f .env ]]; then
  echo "No .env found — copying .env.example."
  cp .env.example .env
  echo "Edit .env and set OPENAI_API_KEY, then re-run ./start.sh"
  exit 1
fi

docker compose up -d --build

echo
echo "Workshop is starting:"
echo "  Workbench      http://localhost/          <- open this"
echo "  (direct: chat UI :3000, docs :3001, api :8000, Redis Insight :5540,"
echo "   Agent Memory Server :8088)"
echo
echo "First boot builds the images and embeds the loan documents (~1 min)."
