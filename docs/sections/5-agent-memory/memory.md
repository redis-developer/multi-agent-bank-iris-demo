# Section 5: Agent memory

## The bot has amnesia <!-- {docsify-ignore} -->

Ask *"what loans do I have?"* then *"foreclose the first one — what would it
cost?"* and the Section 4 bot is lost: each turn hits the graph with a blank
message list, so "the first one" refers to nothing. Worse, come back
tomorrow and it has forgotten you were renovating your home — the cross-sell
moment your sales team would never miss.

LLMs are stateless by construction. Memory is not a model feature — it's an
infrastructure feature. You *could* build it yourself (a message log here, an
extraction prompt there, a vector index for recall, deduplication,
forgetting policies…) and that pile of plumbing is exactly what Redis ships
as a component: the **Agent Memory Server** — the Agent Memory piece of
Redis Iris. It runs beside your app (the `agent-memory` container in this
workshop, a managed service on Redis Cloud) and exposes two tiers of memory
over a small REST API.

## Working memory: the conversation session <!-- {docsify-ignore} -->

Working memory is the ordered message log of one session:
`GET /v1/working-memory/{session_id}` returns the conversation so far,
`PUT` writes it back with the new turn appended. The pipeline fetches it
before running the graph — so every specialist sees the whole conversation —
and appends the turn after replying. A "new chat" is nothing more than a
fresh `session_id`.

## Long-term memory: extracted, not transcribed <!-- {docsify-ignore} -->

Here is the part you *don't* write: as turns land in working memory, the
memory server **automatically extracts durable facts** in the background —
"renovating their home this year", "prefers short tenures" — using its own
LLM, its own embeddings, its own vector index, and stores them against the
`user_id`. Your app's entire long-term memory implementation is one search
call: `POST /v1/long-term-memory/search` with the current message as the
query and the customer as the filter.

Recall is semantic, which is the point: when the customer says "I need some
extra funds", the memory "renovating their home this year" surfaces because
it's *relevant*, not because it's recent — and the sales agent pitches the
home decor loan instead of a generic personal loan. The `user_id` filter is
the privacy boundary: one customer's facts can never surface in another's
conversation.

Compare what Section 3 took (a schema, a vectorizer, a query) with what this
section takes (three HTTP calls) — that difference is what "memory as
infrastructure" means.

[steps](memory-steps.md ':include')

The bot is now smart, grounded, and personal. It is also spending LLM tokens
on the same "what is the foreclosure charge?" question forty times a day.
Time to stop paying for repeat questions.

> **Next section →** [Section 6: Semantic caching](/sections/6-semantic-caching/caching.md)
