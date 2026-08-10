# Section 4: Multi-agent orchestration

## Why five agents beat one <!-- {docsify-ignore} -->

You could write one giant prompt that services loans, issues NOCs, pitches
top-ups, and runs disbursements. It would be long, contradictory ("be a
helpful salesperson" vs "never sell during a complaint"), hand every tool to
every conversation, and be untestable — change the NOC rules and you've
touched the sales pitch too.

The multi-agent pattern splits the bot the way the bank itself is split:
**specialists with narrow prompts and narrow toolboxes**. The servicing agent
can read loans but cannot disburse money. The NOC agent holds exactly three
tools and a hard rule: closed loans only. The journey agent is the only one
that can generate a LAN or initiate disbursement. Small prompts behave
better, and the toolbox *is* the permission model.

## Agents that act: the tool loop <!-- {docsify-ignore} -->

An agent is an LLM in a loop with tools. The model reads the conversation and
either answers or asks for a tool call — `get_customer_loans("CUST1001")` —
your code executes it against Redis, appends the result, and the model looks
again. Think → act → observe, until it can answer. Every account fact in a
reply comes out of a tool result, not the model's imagination — the tools in
`src/agents/tools.py` read and write real Redis state (EMI math, LAN
counters, loan status flips), which is why a disbursement in the chat shows
up in `JSON.GET loan:...` afterwards.

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

The specialists are provided (the tool loop, the RAG node from Section 3, the
supervisor). Your exercise is the orchestration itself: the graph's nodes,
edges, and compilation.

[steps](multi-agent-steps.md ':include')

The team works — but it has amnesia. Ask a follow-up ("and the second one?")
and the bot has no idea what "the second one" is. Memory is next.

> **Next section →** [Section 5: Agent memory](/sections/5-agent-memory/memory.md)
