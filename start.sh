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
echo "  Chat UI        http://localhost:3000"
echo "  Workshop docs  http://localhost:3001"
echo "  API            http://localhost:8000/api/health"
echo "  Redis Insight  http://localhost:5540"
echo
echo "First boot builds the api image and embeds the loan documents (~1 min)."
