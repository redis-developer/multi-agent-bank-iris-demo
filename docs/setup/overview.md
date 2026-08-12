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
- A **Redis Cloud account** (free tier is enough) — set up below
- ~2 GB free RAM for the containers

## Step 0: Set up Redis Cloud

This workshop runs on **your Redis Cloud database from the very first
message** — the FAQ index, the agents' records, memory, everything lives
there, and the Iris services you provision later (**Context Retriever** in
Section 4, **Agent Memory** in Section 5, **LangCache** in Section 6)
attach to it. Do this before booting:

1. Sign up (or sign in) at <https://cloud.redis.io/>.
2. Create a **free database**: **Databases → New database → Free**. The
   free 30MB tier is enough.
3. Open a terminal in the cloned repo and create your `.env` file:

   ```bash
   cp .env.example .env
   ```
4. On the database's page in the console, copy the **public endpoint** and
   the **default user password**, and fill in `.env` — the connection
   string and your OpenAI key while you're there:

   ```bash
   REDIS_URL=redis://default:<password>@<public-endpoint-host>:<port>
   OPENAI_API_KEY=sk-...
   ```

5. Keep the console tab open — Sections 4, 5, and 6 each come back here to
   create their service.

> Service API keys are shown **only once**, at creation time. When a
> section has you create a service, copy the key immediately.
> (If `REDIS_URL` is left unset, the stack falls back to a local Redis
> container — offline mode; the facilitator may use it as a backup.)

## Boot the workshop

With `.env` filled in from Step 0:

```bash
./start.sh
```

First boot builds the images and embeds the FAQ knowledge base into your
database (about a minute). Then open **<http://localhost/>** — the workshop
workbench. Everything lives in one browser tab:

| Where | What |
|---|---|
| **Instructions** (left) | These docs |
| **App** panel | The WhatsApp-style chat UI + pipeline inspector |
| **Code** panel | VS Code, opened on `code/python` |
| **Terminal** panel | A shell at the repo root — `./solve`, `curl`, `redis-cli -h redis` |
| **Redis Insight** panel | Connected to the workshop Redis |

(Each service is also exposed directly — api :8000, chat UI :3000, docs
:3001, Redis Insight :5540, Agent Memory Server :8088 — if you prefer
separate tabs.)

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
