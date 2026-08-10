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

First boot builds the API image and embeds the loan documents into Redis
(about a minute). Then open:

| URL | What |
|---|---|
| <http://localhost:3000> | The WhatsApp-style chat UI + pipeline inspector |
| <http://localhost:3001> | These docs |
| <http://localhost:5540> | Redis Insight, connected to the workshop Redis |
| <http://localhost:8000/api/health> | API health check |
| <http://localhost:8088/v1/health> | Redis Agent Memory Server (used in Section 5) |

## How the exercises work

- You edit files under `code/python/src/`. Five files carry
  `SECTION N` banners — those are the exercise files. Everything else is
  provided and complete.
- The API container runs uvicorn with `--reload`, so most edits apply on
  save. After finishing a section (or running `./solve`), restart the
  pipeline: `docker compose restart api`.
- Stuck, or joining late? Fast-forward any section:

```bash
./solve 3        # apply the Section 3 solution
./solve reset    # back to the starter state
```

## Verify, then begin

Open the chat UI and send *"hello"*. The bot should reply with its
starter fallback message. Head to
[Section 1: Explore the bank](/sections/1-explore-the-bank/explore.md).
