# Setup

## Requirements

- Docker Desktop (or Docker Engine with Compose v2)
- An **OpenAI API key** — used by the chat model (`gpt-4o-mini` by default),
  embeddings (`text-embedding-3-small`), and the Agent Memory Server's own
  extraction LLM
- Ports free: 80 (workbench), 3000 (chat UI), 3001 (docs), 8000 (API),
  8088 (Agent Memory Server), 5540 (Redis Insight), 6379 (Redis)

## Boot

```bash
cp .env.example .env
# edit .env → OPENAI_API_KEY=sk-...
./start.sh                # = docker compose up -d --build
```

First boot: builds the API image (~1–2 min) and seeds Redis — customers,
loans, offers, and the loan documents embedded into `idx:loan_docs`.

Verify: `curl http://localhost:8000/api/health` →
`{"status":"ok","redis":true,"dataset_loaded":true}`.

## Day-to-day commands

```bash
docker compose logs -f api        # watch the pipeline (routing, tools, errors)
./solve <2|3|4|5|6|full|reset>    # apply a solution snapshot (api auto-reloads)
docker compose restart api        # only needed after .env changes — code
                                  # edits reload automatically (uvicorn --reload)
docker compose down               # stop (keeps Redis data volume-free: data
                                  # is reseeded from ./data on next boot)
```

## Resetting state

- **Wipe conversations / NOCs / generated LANs but keep the dataset**: not
  needed usually — restart with `FLUSHALL`:
  ```bash
  docker compose exec redis redis-cli FLUSHALL
  docker compose restart api      # reseeds everything
  ```
- **Back to starter code**: `./solve reset`

## Using a different LLM endpoint

Set in `.env`:

```bash
OPENAI_BASE_URL=https://<your-proxy-or-azure-endpoint>/v1
OPENAI_MODEL=<deployment-or-model-name>
EMBEDDING_MODEL=<embedding-model-name>
EMBEDDING_DIMS=1536      # must match the embedding model
```

Any OpenAI-compatible endpoint works (the workshop uses `langchain-openai`
and RedisVL's `OpenAITextVectorizer`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `set OPENAI_API_KEY in .env` on `docker compose up` | Create `.env` from `.env.example` and set the key |
| Chat UI says "waiting for api…" | First boot embeds the docs; give it ~60s. Check `docker compose logs api` |
| 401 from OpenAI in api logs | Bad/expired key, or your proxy needs `OPENAI_BASE_URL` |
| Replies say "brain is still being built" after solving a section | The reload usually takes 1–2s; check `docker compose logs api` for `Chat pipeline ready`, or `docker compose restart api` |
| Router/cache behave oddly after threshold experiments | Reset thresholds in `.env`, `FLUSHALL`, restart api |
| Section 5: follow-ups work but cross-session recall doesn't | Long-term extraction is a background job — wait a few seconds; check `docker compose logs agent-memory` |
| Port already in use | Change the left-hand port in `docker-compose.yml` |
