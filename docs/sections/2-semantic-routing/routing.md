# Section 2: Semantic routing

## Every message needs a journey <!-- {docsify-ignore} -->

"Where's my NOC?", "what's my EMI?", "I want a top-up" — every WhatsApp
message that arrives must land in the right journey before anything useful
can happen.

Some requests may be generic and suitable for a direct retrieval path. Some may require a user-specific agent and authentication. Some may be irrelevant and should not enter an expensive agent workflow at all.

Asking an LLM to classify every message costs tokens and hundreds of milliseconds *before the
real work even starts*.

## Classification by distance <!-- {docsify-ignore} -->

A semantic router classifies the incoming query by meaning and sends it to the appropriate handler, agent, model, or workflow. It reuses the idea from Section 1: embeddings put similar
meanings close together in vector space. Give each journey a handful of
**reference utterances** — "when is my next EMI due" for servicing, "I need
an NOC for my closed loan" for noc — embed them once into Redis, and routing
becomes a single vector search: embed the incoming message, find the nearest
reference, return its route. One embedding call, sub-millisecond search, no
LLM.

In this section, you'll use RedisVL's `SemanticRouter`.

[steps](routing-steps.md ':include')

The bot now knows *where* every message belongs — it just can't act yet.
Next you ground the `loan_docs` journey in the bank's actual documents.

> **Next section →** [Section 3: RAG over the loan docs](/sections/3-rag-loan-docs/rag.md)
