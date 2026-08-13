# Setup

## Requirements

- Docker Desktop (or Docker Engine with Compose v2)
- An **OpenAI API key** — used by the chat model (`gpt-4o-mini` by default),
  embeddings (`text-embedding-3-small`), and the Agent Memory Server's own
  extraction LLM
- A **Redis Cloud account** (free tier) with a free database — **required**:
  the cloud database is the workshop's only database (there is no local
  Redis container). Section 4 provisions a Context Retriever service,
  Section 5 an Agent Memory service, and Section 6 LangCache, all from
  the console; create the account and database before the workshop
  (Getting started, Step 1)
- Ports free: 80 (workbench), 3000 (chat UI), 3001 (docs), 8000 (API),
  8088 (Agent Memory Server), 5540 (Redis Insight)

## Boot

```bash
cp .env.example .env
# fill in .env → OPENAI_API_KEY=sk-...
#              → REDIS_URL=redis://default:<password>@<host>:<port>
#                (your Redis Cloud database — required, it is THE database)
./start.sh                # = docker compose up -d --build (refuses to boot
                          #   until both keys are filled in)
```

Configure first, boot once: all keys go into `.env` right after cloning
(Getting started, Step 1). First boot seeds the FAQ knowledge base into
your database; the bank's structured records (customers, loans, offers)
arrive in Section 4 through the Context Retriever. The service keys added
mid-workshop (CTX_ADMIN_KEY, LANGCACHE_*) are edited in the Code panel —
the api reloads .env on save.

Verify: `curl http://localhost:8000/api/health` →
`{"status":"ok","redis":true,"dataset_loaded":true}`.

## Day-to-day commands

```bash
docker compose logs -f api        # watch the pipeline (routing, tools, errors)
./solve <2|3|4|5|6|full|reset>    # apply a solution snapshot (api auto-reloads)
# mid-workshop .env edits (CTX_ADMIN_KEY, LANGCACHE_*): open .env in the
# Code panel, save — the api reloads itself. If you ever change REDIS_URL
# or OPENAI_API_KEY after boot: docker compose restart agent-memory
# agent-memory-worker (they re-read .env on restart)
docker compose down               # stop the stack (your data is safe — it
                                  # lives in your Redis Cloud database)
```

## Resetting state

- **Wipe conversations / NOCs / generated LANs**: `FLUSHALL` — note it runs
  against your *cloud* database and also removes Section 4's imported
  records (re-run `python -m src.context.deploy`) and the memory server's
  data:
  ```bash
  docker compose exec terminal sh -c 'redis-cli -u "$REDIS_URL" FLUSHALL'
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
| Section 4: agents say the Context Retriever isn't deployed | Complete `src/context/models.py`, mint the admin key with `python -m src.context.bootstrap` (Terminal; writes `CTX_ADMIN_KEY` to `.env` — api reloads), run `python -m src.context.deploy`, then reload the api |
| Section 4: bootstrap login fails | Wrong password, or the account signs in with Google/SSO (no password for direct login) — mint the key in the console instead: Context Retriever → Create with CLI, paste it into `.env` as `CTX_ADMIN_KEY` |
| Section 6: "LangCache is not configured" in api logs | Set `LANGCACHE_URL` / `LANGCACHE_CACHE_ID` / `LANGCACHE_API_KEY` in `.env` (Code panel, save — api reloads) |
| Section 6: 401/403 from LangCache | The service key is shown only once at creation — generate a new key from the service's page in the Redis Cloud console |
| Section 5: follow-ups work but cross-session recall doesn't | Long-term extraction is a background job — wait a few seconds; check `docker compose logs agent-memory` |
| Port already in use | Change the left-hand port in `docker-compose.yml` |
