# Section 2: Semantic routing

## Every message needs a journey <!-- {docsify-ignore} -->

"Where's my NOC?", "what's my EMI?", "I want a top-up" — every WhatsApp
message that arrives must land in the right journey before anything useful
can happen. The classic answers are all bad in their own way: keyword rules
shatter on paraphrase ("closure certificate" vs "NOC"), intent-classifier
models need training data and an MLOps pipeline, and asking an LLM to
classify every message costs tokens and hundreds of milliseconds *before the
real work even starts*.

## Classification by distance <!-- {docsify-ignore} -->

Semantic routing reuses the idea from Section 1: embeddings put similar
meanings close together in vector space. Give each journey a handful of
**reference utterances** — "when is my next EMI due" for servicing, "I need
an NOC for my closed loan" for noc — embed them once into Redis, and routing
becomes a single vector search: embed the incoming message, find the nearest
reference, return its route. One embedding call, sub-millisecond search, no
LLM.

The `distance_threshold` is the honesty knob. A message close to a route's
references (small distance) routes confidently; a message that isn't close
to *anything* — "what's the weather" — matches no route, and the router says
so by returning nothing. That "I don't know" is a feature: in Section 4 the
supervisor uses the LLM as the *fallback* classifier for exactly those
messages, so you pay for LLM judgment only when the cheap path abstains.

This is RedisVL's `SemanticRouter`, and it's the front door of the whole
pipeline: every message is classified before any agent sees it. The router
ships **already built** in this workshop — this section is a guided read of
the code and a test drive, so you understand exactly what the front door is
doing before you start building the rooms behind it.

[steps](routing-steps.md ':include')

The bot now knows *where* every message belongs — it just can't act yet.
Next you ground the `loan_docs` journey in the bank's actual documents.

> **Next section →** [Section 3: RAG over the loan docs](/sections/3-rag-loan-docs/rag.md)
