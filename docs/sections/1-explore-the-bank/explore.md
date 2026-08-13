# Section 1: Explore the bank

## Your database, before the bank moves in <!-- {docsify-ignore} -->

Everything in this workshop runs against the Redis Cloud database you
connected in Step 1. Right now it holds exactly one thing, seeded at boot:
the bank's **FAQ knowledge base** — ~20 question/answer pairs covering
rates, foreclosure, top-ups, balance transfers, NOCs, documents, and
disbursement. Each FAQ is stored with its text, a `product` tag, and a
1536-dimension **embedding** of its meaning, all indexed in `idx:faqs`.

That index is the raw material for Section 3's RAG: vector search finds
FAQs by *what they mean*, not what they literally say — "how much to close
my loan early" lands on the foreclosure answer even though the word
"foreclosure" never appears in the question.

Notice what's *not* in the database yet: no customers, no loans, no
offers. The bank's structured records arrive in **Section 4**, imported
through the **Redis Context Retriever** — the same way RDI would feed them
from core banking in production. Until then the bot can talk *about* loans
(FAQs) but knows nothing about *your* loans. Watching that gap close is
the arc of the workshop.

## The starter bot <!-- {docsify-ignore} -->

The chat pipeline (`code/python/src/chat/service.py`) is mostly a shell.
The agent-framework pieces — the semantic router and the LangGraph
multi-agent graph — ship already working; what *you* build is the Redis
Iris context layer:

| File | Section |
|---|---|
| `src/router/semantic_router.py` | 2 — **provided**: read & test it |
| `src/chat/service.py` | 3, 4, 5, 6 — the pipeline call-sites |
| `src/retrieval/rag.py` | 3 — keyword & hybrid search (going deeper) |
| `src/context/models.py` | 4 — the Context Retriever's semantic model |
| `src/context/deploy.py` | 4 — build the context surface |
| `src/memory/redis_memory.py` | 5 — agent memory |
| `src/cache/semantic_cache.py` | 6 — semantic caching |
| `src/agents/graph.py` | **provided** plumbing — skim if curious |

[steps](explore-steps.md ':include')

The knowledge base is ready. Next: teach the bot to recognise *which
journey* each message belongs to — without spending a single LLM token.

> **Next section →** [Section 2: Semantic routing](/sections/2-semantic-routing/routing.md)
