# Section 6: Semantic caching

## Paying full price for repeat questions <!-- {docsify-ignore} -->

"What is the foreclosure charge?", "foreclosure fees?", "how much to close my
loan early?" — at WhatsApp scale, a bank answers this *thousands of times a
day*, and right now every single one runs the full pipeline: an embedding, a
vector search, and an LLM generation. Same answer, full price, every time.

A classic cache can't help, because no two customers phrase the question
identically and an exact-match key never hits. But you already own the
solution: embeddings. Cache the answer under the *meaning* of its question —
the embedding — and any paraphrase within a distance threshold is a hit,
served straight from Redis in a few milliseconds, zero tokens. That's a
**semantic cache** (RedisVL's `SemanticCache`; Redis LangCache is the same
pattern as a managed service, and reports token savings up to ~90% on
FAQ-heavy traffic).

## What may be cached is a policy decision <!-- {docsify-ignore} -->

The threshold tension from Section 2 returns sharper here: too loose and
"foreclosure charge on *personal* loans" could serve the *home decor* answer
— a wrong answer delivered confidently and cheaply. Start strict
(`CACHE_DISTANCE_THRESHOLD=0.13`), measure the hit rate, loosen carefully.

And there's a second rule that matters more than the threshold: **only
impersonal answers may be cached**. The loan_docs agent's policy answers are
the same for everyone — cacheable. "What's *my* outstanding balance?" is one
customer's data; cache it and you will eventually show it to someone else.
The pipeline enforces this by caching only replies whose `agent` is
`loan_docs`. In production you'd go further (TTLs, invalidation on policy
updates), but the shape is the same.

The cache check runs *before everything* — router, memory, graph — because
work you skip is the only work that's free.

[steps](caching-steps.md ':include')

That's the full pipeline. Time to step back and look at what you built.

> **Next section →** [Section 7: Wrap-up](/sections/7-wrap-up/wrap-up.md)
