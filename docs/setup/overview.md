# Getting started

This is a hands-on, 2–3 hour workshop. You build the brain of a WhatsApp
loan-servicing bot for a retail bank, one Redis capability per section.

## The scenario

Your bank runs its customer conversations on WhatsApp. One number, many
journeys:

| Journey | Who handles it | What it covers |
|---|---|---|
| **servicing** | Servicing agent | Loan status, balances, EMI dates for existing customers |
| **loan_docs** | RAG agent | Policy questions answered from the bank's loan documents |
| **noc** | NOC agent | No Objection Certificates — only for closed loans |
| **sales** | Sales agent | Top-up loans, balance transfers, home decor loans, cross-sell |
| **journey** | Journey agent | EMI quotes → documents → LAN → disbursement, end to end |

The bot starts the workshop with none of this wired up. Section by section you
add: **semantic routing** (2), **RAG** (3), **multi-agent orchestration with
LangGraph** (4), **agent memory** (5), and **semantic caching** (6) — the
component stack of [Redis Iris](https://redis.io/iris/).

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- An OpenAI API key (used for the LLM **and** embeddings)
- A **Redis Cloud account** (free tier is enough) — set up in Step 1
- ~2 GB free RAM for the containers

## Step 1: Clone and configure

Everything the workshop needs is set up once, right after cloning:

1. Clone the repo and create your `.env` from the template:

   ```bash
   git clone <this-repo> && cd multi-agent-bank-iris-demo
   cp .env.example .env
   ```

2. Sign up (or sign in) at <https://cloud.redis.io/> and create a **free
   database**: **Databases → New database → Free**. The free 30MB tier is
   enough. Keep the console tab open — Sections 4, 5, and 6 come back
   here to create their Iris services (Context Retriever, Agent Memory,
   LangCache).

3. Fill in `.env` with your two keys — your OpenAI key, and the
   connection string from your database's page in the console (public
   endpoint + default-user password):

   ```bash
   OPENAI_API_KEY=sk-...
   REDIS_URL=redis://default:<password>@<public-endpoint-host>:<port>
   ```

   The workshop runs on **your Redis Cloud database**: the FAQ index, the
   agents' records, memory, and the Iris services all attach to it.

## Step 2: Boot the workshop

```bash
./start.sh
```

First boot builds the images and seeds the FAQ knowledge base into your
database (~1–2 min). Then open **<http://localhost/>** — the workshop
workbench. From here on, everything happens in this one browser tab:

| Where | What |
|---|---|
| **Instructions** (left) | These docs |
| **App** panel | The WhatsApp-style chat UI + pipeline inspector |
| **Code** panel | VS Code, opened on `code/python` |
| **Terminal** panel | A shell at the repo root — `./solve`, `curl`, `redis-cli -u "$REDIS_URL"` (your cloud database) |
| **Redis Insight** panel | Browse your cloud database (added once in Section 1, step 1) |

(Each service is also exposed directly — api :8000, chat UI :3000, docs
:3001, Redis Insight :5540, Agent Memory Server :8088 — if you prefer
separate tabs.)

> The service keys you create later (Sections 4 and 6) go into `.env` too
> — it's editable right in the **Code** panel at the workspace root, and
> the api reloads itself when you save. Service API keys are shown **only
> once**, at creation time: copy them immediately.
> Both keys in Step 1 are **required** — `./start.sh` refuses to boot
> until they're filled in. There is no local Redis: your cloud database
> is the workshop's only database.

## How the exercises work

- You edit files under `code/python/src/` in the **Code** panel. The
  exercises are pure Redis Iris context layer — retrieval (3), the context
  retriever (4), agent memory (5), semantic caching (6) — in files carrying
  `SECTION N` banners. The agent-framework code (the semantic router, the
  LangGraph multi-agent graph) is provided: Section 2 reads the router, and
  the graph is invisible plumbing you switch on with one line in Section 4.
- The api runs uvicorn with `--reload`: saving a file rebuilds the whole
  pipeline in a second or two. No restarts needed.
- Stuck, or joining late? Fast-forward any section from the **Terminal**
  panel:

```bash
./solve 3        # apply the Section 3 solution
./solve reset    # back to the starter state
```

## Verify, then begin

Open the chat UI and send *"hello"*. The bot should reply with its
starter fallback message. Head to
[Section 1: Explore the bank](/sections/1-explore-the-bank/explore.md).
