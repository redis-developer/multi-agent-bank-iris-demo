# Section 1: Explore the bank

## One database, four shapes of data <!-- {docsify-ignore} -->

Everything the bot will need this workshop is already in Redis — the same
Redis, four different shapes:

- **Customer profiles** are hashes (`customer:CUST1001`) — flat field/value
  lookups at key-access speed.
- **Loans** are JSON documents (`loan:LAN20240001`) — nested, queryable, and
  updatable in place (a disbursement flips `$.status` without rewriting the
  document).
- **Pre-approved offers** are JSON arrays per customer (`offers:CUST1001`),
  refreshed by the bank's risk models.
- **Loan policy documents** — the PDFs your customers ask questions about —
  are chunked by section, embedded, and stored in the vector index
  `idx:loan_docs`.

That last one powers most of this workshop. Each chunk holds its text, its
source document, a `product` tag, and a 1536-dimension embedding of its
meaning. Vector search finds chunks by *what they mean*, not what they
literally say: "how much to close my loan early" lands on the foreclosure
section even though the word "foreclosure" never appears in the question.

In production this loading pipeline is the job of ingestion (and Redis Data
Integration keeps operational data in sync continuously). Here, the API
container seeded everything on first boot so you can focus on the agent side.

## The starter bot <!-- {docsify-ignore} -->

The chat pipeline (`code/python/src/chat/service.py`) is mostly a shell.
The agent-framework pieces — the semantic router and the LangGraph
multi-agent graph — ship already working, with guided reads in Sections 2
and 4. What *you* build is the Redis context layer:

| File | Section |
|---|---|
| `src/router/semantic_router.py` | 2 — **provided**: read & test it |
| `src/chat/service.py` | 3, 4, 5, 6 — the pipeline call-sites |
| `src/retrieval/rag.py` | 3 — keyword & hybrid search (going deeper) |
| `src/agents/graph.py` | 4 — **provided**: the multi-agent graph, read & test it |
| `src/memory/redis_memory.py` | 5 — agent memory |
| `src/cache/semantic_cache.py` | 6 — semantic caching |

[steps](explore-steps.md ':include')

The data layer is ready. Next: teach the bot to recognise *which journey*
each message belongs to — without spending a single LLM token.

> **Next section →** [Section 2: Semantic routing](/sections/2-semantic-routing/routing.md)
