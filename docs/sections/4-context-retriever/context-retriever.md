# Section 4: The Context Retriever

From this section on, every message is handled by a team of five
specialists — servicing, loan_docs, noc, sales, journey — orchestrated by a
supervisor that trusts the Section 2 route and asks the LLM only when the
router abstained:

```
        START ─► supervisor ─► one specialist ─► END
```

All of that is **provided** (`src/agents/graph.py`, `src/agents/personas.py`
— skim them if you're curious). You'll switch the team on with one line.
This section's real subject is the layer the team *reads the bank through*.

## The tool zoo problem <!-- {docsify-ignore} -->

Look at what the agents need to know: profiles, loans, offers. The obvious
approach is a hand-written tool per question — `get_customer_profile`,
`get_customer_loans`, `get_loan_details`, `get_preapproved_offers`… four
today; then someone needs cards, then disputes, then branches, and every
agent team writes its own variants. That sprawl has a name — the **tool
zoo** — and it comes with a worse problem: every one of those tools trusts
the LLM to pass the right `customer_id`. A prompt that says *"never act for
another customer"* is a policy written in hope.

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

[steps](context-retriever-steps.md ':include')

The team works, and reads the bank through a governed model. But it has
amnesia — ask a follow-up ("and the second one?") and the bot has no idea
what "the second one" is. Memory is next.

> **Next section →** [Section 5: Agent memory](/sections/5-agent-memory/memory.md)
