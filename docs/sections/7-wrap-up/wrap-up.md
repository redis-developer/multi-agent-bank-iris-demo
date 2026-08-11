# Section 7: Wrap-up

## What you built <!-- {docsify-ignore} -->

A WhatsApp loan-servicing bot for a bank, whose every message flows:

```
message ─► semantic cache ─► semantic router ─► recall memories
              (Section 6)       (Section 2)       (Section 5)
                                     │
                                     ▼
                        LangGraph supervisor (Section 4)
             servicing · loan_docs(RAG §3) · noc · sales · journey
                                     │
                                     ▼
              remember facts ─► store in cache ─► reply
```

Every arrow in that diagram is Redis:

| Capability | What Redis holds | Where you built it |
|---|---|---|
| Operational data | customer hashes, loan JSON, offers | Section 1 (seeded) |
| Vector retrieval | `idx:loan_docs` — embedded policy chunks | Sections 1 & 3 |
| Semantic routing | `wa-journey-router` reference embeddings | Section 2 |
| Governed retrieval | the context retriever's entity model over customer/loan/offer records | Section 4 |
| Tool state | LAN counter, loan status, NOC records | Section 4 |
| Working memory | Agent Memory Server sessions (per `session_id`) | Section 5 |
| Long-term memory | Agent Memory Server auto-extracted facts (per `user_id`) | Section 5 |
| Semantic cache | **LangCache** service on Redis Cloud (cache-aside REST) | Section 6 |

One database serving seven different jobs is the actual lesson: the agent
stack's *context problem* — what does the model get to read, at what cost,
at what latency — is a data problem, and it's all hot data.

## From workshop to production: Redis Iris <!-- {docsify-ignore} -->

Everything you hand-built has a managed counterpart in
[Redis Iris](https://redis.io/iris/), Redis's real-time context engine for
agents:

- **Redis LangCache** — you already used it: Section 6's cache *is* the
  managed service, provisioned from the Redis Cloud console, with
  threshold tuning and hit-rate analytics built in.
- **Redis Agent Memory** — you used both forms: Section 5 built against
  the self-hosted Agent Memory Server, then provisioned the managed
  service on Redis Cloud (TTLs, extraction cadence, summarization, custom
  memory types, sensitive-data exclusions).
- **Redis Context Retriever** — Section 4's miniature, productised: model
  entities with the `ctxctl` CLI or the Cloud UI, and the generated tools
  are served over MCP with scoped agent keys and access tags
  (`pip install redis-context-retriever`).
- **Redis Data Integration (RDI)** — the pipeline we faked with a seed
  script: CDC that keeps Redis continuously in sync with core banking
  systems, so agents act on live data.

## Where to take this bot next <!-- {docsify-ignore} -->

- **Real WhatsApp**: put the `/api/chat` endpoint behind the WhatsApp
  Business API webhook — the pipeline doesn't change.
- **Streaming + human handoff**: LangGraph supports interrupts; route
  low-confidence or high-value journeys (disbursement!) to a human queue.
- **Guardrails**: add a compliance-check node after every agent, and TTL +
  invalidation on the semantic cache tied to policy-document updates.
- **Observability**: the inspector panel's fields (route, agent, cached,
  latency) are exactly what you'd ship to your metrics stack.

## Keep learning <!-- {docsify-ignore} -->

- [Redis Iris](https://redis.io/iris/) · [Getting started with Redis Iris](https://redis.io/tutorials/getting-started-with-redis-iris/)
- [RedisVL documentation](https://docs.redisvl.com)
- [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- [Redis University](https://university.redis.io)

Thanks for building with us. 🚀
