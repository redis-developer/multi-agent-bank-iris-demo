#!/usr/bin/env bash
# One-command boot for the workshop.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from the template. Fill it in, then re-run ./start.sh:"
  echo "  OPENAI_API_KEY   your OpenAI key (LLM + embeddings)"
  echo "  REDIS_URL        your Redis Cloud database connection string"
  echo "                   (console -> your database -> public endpoint)"
  exit 1
fi

docker compose up -d --build

echo
echo "Workshop is starting:"
echo "  Workbench      http://localhost/          <- open this"
echo "  (direct: chat UI :3000, docs :3001, api :8000, Redis Insight :5540,"
echo "   Agent Memory Server :8088)"
echo
echo "First boot builds images and seeds the FAQ knowledge base (~1-2 min)."
