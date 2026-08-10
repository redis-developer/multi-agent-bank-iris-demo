# Multi-agent Bank Bot — a Redis Iris Workshop

A 2–3 hour, instructor-led, hands-on workshop. Participants build the brain
of a **WhatsApp loan-servicing bot** for a retail bank using **Redis,
LangChain, and LangGraph** — one Redis Iris component per section:

| Section | You build | Redis component |
|---|---|---|
| 1. Explore the bank | — (data walkthrough) | Hashes, JSON, vector index |
| 2. Semantic routing | Route WA messages into journeys | RedisVL `SemanticRouter` |
| 3. RAG over loan docs | Grounded policy answers with citations | RedisVL vector search |
| 4. Multi-agent orchestration | Supervisor + 5 specialist agents with tools | LangGraph + Redis as tool state |
| 5. Agent memory | Session threads + auto-extracted customer facts | **Redis Agent Memory Server** (the Iris Agent Memory component) |
| 6. Semantic caching | Zero-token answers for repeat questions | RedisVL `SemanticCache` |
| 7. Wrap-up | — | Map to Redis Iris (LangCache, Agent Memory, Context Retriever, RDI) |

## The use case

One WhatsApp number, five journeys, five agents:

- **servicing** — existing customers: loan status, balances, EMI dates
- **loan_docs** — loan policy Q&A grounded in the bank's loan documents (RAG)
- **noc** — No Objection Certificates, issued only for closed loans
- **sales** — top-up loans, balance transfers, home decor loans, personal-loan
  cross-sell, pre-approved offers
- **journey** — end-to-end loan journey: EMI/interest calculation, benefits
  vs considerations, document qualification, LAN generation, disbursement

Agent tools read and write real Redis state — LANs come from a Redis counter,
disbursement flips loan status, NOCs are recorded — so the chat behaves like
a live servicing system.

## Quick start

```bash
git clone <this-repo>
cd multi-agent-bank-iris-demo
cp .env.example .env        # set OPENAI_API_KEY
./start.sh
```

Then open:

- **Chat UI + pipeline inspector** — <http://localhost:3000>
- **Workshop docs** — <http://localhost:3001>
- **Redis Insight** — <http://localhost:5540>
- **API** — <http://localhost:8000/api/health>
- **Agent Memory Server** — <http://localhost:8088/v1/health>

## Repository layout

```
code/python/        the app participants edit (5 files carry SECTION banners)
code/web/           WhatsApp-style chat UI + pipeline inspector
data/               seed dataset: customers, loans, offers, loan documents
docs/               Docsify workshop guide (sections 1–7 + reference)
solutions/python/   per-section solution snapshots (starter, 2, 3, 4, 5, 6)
docker/             container build files
solve               fast-forward: ./solve 3 | ./solve full | ./solve reset
```

## Exercises and solutions

Participants edit the five exercise files under `code/python/src/`; each
`SECTION N` banner marks a stub. Solutions are full-file snapshots per
section, applied with:

```bash
./solve 4        # jump to the end of Section 4
./solve reset    # back to the starter
```

See [FACILITATOR.md](FACILITATOR.md) for run-of-show and
[SETUP.md](SETUP.md) for detailed setup and troubleshooting.
