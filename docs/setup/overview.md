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
- ~2 GB free RAM for the containers

## Boot the workshop

```bash
cp .env.example .env      # then set OPENAI_API_KEY
./start.sh
```

First boot builds the images and embeds the loan documents into Redis
(about a minute). Then open **<http://localhost/>** — the workshop
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

- You edit files under `code/python/src/` in the **Code** panel. Five files
  carry `SECTION N` banners — those are the exercise files. Everything else
  is provided and complete.
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
