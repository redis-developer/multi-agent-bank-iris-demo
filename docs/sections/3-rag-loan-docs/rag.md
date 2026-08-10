# Section 3: RAG over the loan docs

## The model doesn't know your bank <!-- {docsify-ignore} -->

Ask a bare LLM "what is the foreclosure charge on a personal loan?" and it
will answer — fluently, confidently, and from *some other bank's* general
knowledge. Your foreclosure charge is 4% after 6 EMIs, nil for floating-rate
loans, NOC within 15 working days. None of that is in the model's training
data, and in a regulated industry, a made-up number in a customer chat is not
a quirk — it's a compliance incident.

## Retrieve, augment, generate <!-- {docsify-ignore} -->

The fix is to stop treating the model as a knowledge base and start treating
it as a *reader*. The model's context — the text it reads before replying —
is yours to compose. Put the right passage from the right policy document in
front of the question, and the model answers from it.

That's retrieval-augmented generation (RAG), three moves:

- **Retrieve** — embed the customer's question and run a vector search over
  `idx:loan_docs` (the index you explored in Section 1). The chunks that come
  back are the passages closest in meaning to the question.
- **Augment** — lay those chunks into the prompt as numbered context entries
  ahead of the question.
- **Generate** — the model answers *from the passages*, citing them like
  `[1]`, `[2]` — and says so when the passages don't contain the answer.

The system prompt (the `loan_docs` persona in `src/agents/personas.py`) is
already written to enforce grounding: answer strictly from context, cite
passages, never guess. What's missing is the plumbing that gets the context
there — that's this section's exercise, in the `loan_docs` branch of the chat
pipeline.

[steps](rag-steps.md ':include')

One journey is now genuinely useful. But servicing, NOC, sales, and the loan
journey need more than reading — they need to *act*: look up accounts, check
eligibility, generate LANs. That takes agents with tools.

> **Next section →** [Section 4: Multi-agent orchestration](/sections/4-multi-agent/multi-agent.md)
