# Setup

## Requirements

- Docker Desktop (or Docker Engine with Compose v2)
- An **OpenAI API key** — used by the chat model (`gpt-4o-mini` by default),
  embeddings (`text-embedding-3-small`), and the Agent Memory Server's own
  extraction LLM
- A **Redis Cloud account** (free tier) with a free database — Section 4
  provisions a Context Retriever service, Section 5 an Agent Memory
  service, and Section 6 LangCache, all from the console; create the
  account and database before the workshop (Getting started, Step 0)
- Ports free: 80 (workbench), 3000 (chat UI), 3001 (docs), 8000 (API),
  8088 (Agent Memory Server), 5540 (Redis Insight), 6379 (Redis)

## Boot

```bash
cp .env.example .env
# edit .env → OPENAI_API_KEY=sk-...
#            → REDIS_URL=redis://default:<password>@<host>:<port>
#              (your Redis Cloud database; unset = local fallback container)
./start.sh                # = docker compose up -d --build
```

First boot: builds the API image (~1–2 min) and seeds your database with
the FAQ knowledge base, embedded into `idx:faqs`. The bank's structured
records (customers, loans, offers) arrive in Section 4 through the Context
Retriever.

Verify: `curl http://localhost:8000/api/health` →
`{"status":"ok","redis":true,"dataset_loaded":true}`.

## Day-to-day commands

```bash
docker compose logs -f api        # watch the pipeline (routing, tools, errors)
./solve <2|3|4|5|6|full|reset>    # apply a solution snapshot (api auto-reloads)
docker compose up -d api          # after .env changes (recreates the api with
                                  # the new values — `restart` keeps old ones;
                                  # code edits reload automatically)
docker compose down               # stop (keeps Redis data volume-free: data
                                  # is reseeded from ./data on next boot)
```

## Resetting state

- **Wipe conversations / NOCs / generated LANs**: `FLUSHALL` — note it runs
  against your *cloud* database and also removes Section 4's imported
  records (re-run `python -m src.context.deploy`) and the memory server's
  data:
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
| Replies say "brain is still being built" after solving a section | The reload usually takes 1–2s; check `docker compose logs api` for `Chat pipeline ready`, or restart with `docker compose restart api` |
| Router behaves oddly after threshold experiments | Reset thresholds in `.env`, `FLUSHALL`, restart api |
| Section 4: agents say the Context Retriever isn't deployed | Complete `src/context/models.py`, set `CTX_ADMIN_KEY` in `.env` (`docker compose up -d api`), run `python -m src.context.deploy` from the Terminal, then reload the api |
| Section 6: "LangCache is not configured" in api logs | Set `LANGCACHE_URL` / `LANGCACHE_CACHE_ID` / `LANGCACHE_API_KEY` in `.env`, then `docker compose up -d api` |
| Section 6: 401/403 from LangCache | The service key is shown only once at creation — generate a new key from the service's page in the Redis Cloud console |
| Section 5: follow-ups work but cross-session recall doesn't | Long-term extraction is a background job — wait a few seconds; check `docker compose logs agent-memory` |
| Port already in use | Change the left-hand port in `docker-compose.yml` |
