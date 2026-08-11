# Section 4: Agents & the Context Retriever

## Why five agents beat one <!-- {docsify-ignore} -->

You could write one giant prompt that services loans, issues NOCs, pitches
top-ups, and runs disbursements. It would be long, contradictory ("be a
helpful salesperson" vs "never sell during a complaint"), hand every tool to
every conversation, and be untestable — change the NOC rules and you've
touched the sales pitch too.

The multi-agent pattern splits the bot the way the bank itself is split:
**specialists with narrow prompts and narrow toolboxes**. The servicing agent
can read loans but cannot disburse money. The journey agent is the only one
that can generate a LAN or initiate disbursement. Small prompts behave
better, and the toolbox *is* the permission model.

The whole LangGraph orchestration — specialists, tool loop, supervisor,
wiring — is **provided**: this workshop's exercises are the Redis context
layer, not the agent framework. What you build in this section is the layer
the agents *read through*.

## The tool zoo problem <!-- {docsify-ignore} -->

Look at what the agents need to know about the bank: profiles, loans,
offers. The obvious approach is a hand-written tool per question —
`get_customer_profile`, `get_customer_loans`, `get_loan_details`,
`get_preapproved_offers`… four today; then someone needs cards, then
disputes, then branches, and every agent team writes its own variants. That
sprawl has a name — the **tool zoo** — and it comes with a worse problem:
every one of those tools trusts the LLM to pass the right `customer_id`. A
prompt that says *"never act for another customer"* is a policy written in
hope.

## Schema-first, governed retrieval <!-- {docsify-ignore} -->

Redis Iris's **Context Retriever** inverts the tool zoo. You declare the
*semantic model* of your business data once — entities, fields, key
patterns, ownership, relationships — and the retrieval tools are
**generated from the model**. Three consequences:

- **One definition, consistent surface.** Adding "cards" to the bot becomes
  declaring an entity, not writing and reviewing another tool.
- **Agents stay out of the database.** They call generated tools that
  follow the declared entity paths — no hand-rolled queries, no guessing.
- **Governance by design, not by prompt.** Access rules live in the
  retriever: every fetch is scoped to the verified customer, *row by row*.
  An agent asking for someone else's loan is refused by the data layer —
  even if the LLM was talked into asking.

This section's exercise builds a working miniature of that idea in
`src/context/retriever.py`: an `ENTITIES` model, a generated tool surface,
and row-level governance. The managed version on Redis Cloud does the same
as a service — `pip install redis-context-retriever`, model entities with
the `ctxctl` CLI or the Cloud UI, and agents call the generated tools over
MCP with scoped agent keys and access tags.

## The supervisor graph <!-- {docsify-ignore} -->

LangGraph assembles the team as an explicit state machine — nodes that share
a typed state, edges that decide who runs:

```
                   START
                     │
                supervisor        ← trusts the Section 2 route;
                     │              asks the LLM only when it abstained
  ┌─────────┬────────┼─────────┬───────────┐
servicing  loan_docs noc     sales      journey
  └─────────┴────────┴─────────┴───────────┘
                     │
                    END
```

Note the economics of the supervisor: the semantic router already classified
the message for the cost of one embedding. The supervisor only spends an LLM
call on messages the router abstained on. Cheap path first, smart path as
fallback — a pattern worth stealing for production.

[steps](multi-agent-steps.md ':include')

The team works, and reads the bank through a governed model. But it has
amnesia — ask a follow-up ("and the second one?") and the bot has no idea
what "the second one" is. Memory is next.

> **Next section →** [Section 5: Agent memory](/sections/5-agent-memory/memory.md)
