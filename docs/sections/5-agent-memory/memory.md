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
forgetting policies…) and that pile of plumbing is exactly what Redis runs
for you: **Agent Memory**, a managed Redis Iris service you provision in the
Redis Cloud console — like the Context Retriever in Section 4 and LangCache
in Section 6. It exposes two tiers of memory over a small REST API, plus
the production controls you'd never get around to building: per-tier TTLs,
extraction cadence, automatic session summarization, custom memory types,
and sensitive-data exclusions.

## Session memory: the conversation event log <!-- {docsify-ignore} -->

Session memory is the ordered event log of one conversation:
`POST /v1/stores/{storeId}/session-memory/events` appends each message as
an event, `GET …/session-memory/{sessionId}` returns the conversation so
far. The pipeline fetches it before running the graph — so every specialist
sees the whole conversation — and appends the turn after replying. A "new
chat" is nothing more than a fresh `sessionId`. The session's **owner** is
taken from the first event's `actorId` — which is why the customer's
message carries their `customer_id`.

## Long-term memory: extracted, not transcribed <!-- {docsify-ignore} -->

Here is the part you *don't* write: as events land in session memory, the
service **automatically extracts durable facts** in the background —
"renovating their home this year", "prefers short tenures" — using its own
LLM, its own embeddings, its own vector index, and stores them against the
session's owner. Your app's entire long-term memory implementation is one
search call: `POST …/long-term-memory/search` with the current message as
the query and the customer as the `ownerId` filter.

Recall is semantic, which is the point: when the customer says "I need some
extra funds", the memory "renovating their home this year" surfaces because
it's *relevant*, not because it's recent — and the sales agent pitches the
home decor loan instead of a generic personal loan. The `ownerId` filter is
the privacy boundary: one customer's facts can never surface in another's
conversation.

Compare what Section 3 took (a schema, a vectorizer, a query) with what this
section takes (two payloads over HTTPS) — that difference is what "memory
as a managed service" means.

[steps](memory-steps.md ':include')

The bot is now smart, grounded, and personal. It is also spending LLM tokens
on the same "what is the foreclosure charge?" question forty times a day.
Time to stop paying for repeat questions.

> **Next section →** [Section 6: Semantic caching](/sections/6-semantic-caching/caching.md)
