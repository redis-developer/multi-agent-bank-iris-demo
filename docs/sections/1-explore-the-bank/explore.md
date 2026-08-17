# Section 1: Explore the bank

## Your database, before the bank moves in <!-- {docsify-ignore} -->

In the beginning, after seeding the database - your Redis Cloud instance only contains the bank's **FAQ knowledge base** — ~20 question/answer pairs containing
rates, foreclosure, top-ups, balance transfers, NOCs, documents, and
disbursement info. Each FAQ is stored with its text, a `product` tag, and a
1536-dimension **vector embeddings embedding**, all indexed in `idx:faqs`.

In Section 3, you'll use this index to do a vector search. Your bot can talk *about* loans (FAQs) but knows nothing about *your* loans yet. You'll implement this in **Section 4**.

## The starter bot <!-- {docsify-ignore} -->

The chat pipeline (`code/python/src/chat/service.py`) is mostly a shell.
The agent-framework pieces — the semantic router and the LangGraph
multi-agent graph — ship already working; what *you* build is the Redis
Iris context layer:

| File | Section |
|---|---|
| `src/router/semantic_router.py` | 2 — **provided**: read & test it |
| `src/chat/service.py` | 4, 5, 6 — the pipeline call-sites |
| `src/retrieval/rag.py` | 3 — vector, keyword & hybrid search |
| `src/context/models.py` | 4 — the Context Retriever's semantic model |
| `src/context/deploy.py` | 4 — build the context surface |
| `src/memory/redis_memory.py` | 5 — agent memory |
| `src/cache/semantic_cache.py` | 6 — semantic caching |
| `src/agents/graph.py` | **provided** plumbing — skim if curious |

[steps](explore-steps.md ':include')

The knowledge base is ready. Next: teach the bot to recognise *which
journey* each message belongs to — without spending a single LLM token.

> **Next section →** [Section 2: Semantic routing](/sections/2-semantic-routing/routing.md)
