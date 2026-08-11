# Section 6: Semantic caching with LangCache

## Paying full price for repeat questions <!-- {docsify-ignore} -->

"What is the foreclosure charge?", "foreclosure fees?", "how much to close my
loan early?" — at WhatsApp scale, a bank answers this *thousands of times a
day*, and right now every single one runs the full pipeline: an embedding, a
vector search, and an LLM generation. Same answer, full price, every time.

A classic cache can't help, because no two customers phrase the question
identically and an exact-match key never hits. The fix is a **semantic
cache**: store each answer under the *meaning* of its question — its
embedding — and any paraphrase above a similarity threshold is a hit, served
straight from the cache. No retrieval, no generation, zero tokens.

## LangCache: the cache as a service <!-- {docsify-ignore} -->

This section uses **Redis LangCache**, the managed semantic-caching service
of Redis Iris — you create it in the Redis Cloud console during the steps
below. The division of labour is the point:

- **The service owns the hard parts** — the embedding model, the vector
  index, similarity search, TTLs, and hit-rate analytics.
- **Your app owns two REST calls** — the classic *cache-aside* pattern:
  `search` before doing any work; on a miss, do the work and `set` the
  result so the next paraphrase hits.

Notice what disappeared from your code compared to everything you built so
far: no vectorizer, no schema, no index. A cache hit doesn't even call
OpenAI — LangCache embeds the prompt itself, inside the service.

## What may be cached is a policy decision <!-- {docsify-ignore} -->

Two dials govern a semantic cache in production:

- **The similarity threshold** (0–1, higher = stricter). Too loose and
  "foreclosure charge on *personal* loans" could serve the *home decor*
  answer — a wrong answer delivered confidently and cheaply. A useful
  starting map: `0.95+` for near-exact only, `0.9` as a balanced default,
  `0.8` for FAQ-style deduplication. This workshop defaults to `0.85` and
  the steps let you break it on purpose.
- **What is allowed in at all.** Only impersonal answers may be cached:
  loan-policy answers are the same for every customer; "what's *my*
  outstanding balance" is one customer's data — cache it and you will
  eventually show it to someone else. The pipeline enforces this by caching
  only replies whose `agent` is `loan_docs`.

The cache check runs *before everything* — router, memory, graph — because
work you skip is the only work that's free.

[steps](caching-steps.md ':include')

That's the full pipeline. Time to step back and look at what you built.

> **Next section →** [Section 7: Wrap-up](/sections/7-wrap-up/wrap-up.md)
