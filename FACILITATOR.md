# Facilitator guide

## Format

Instructor-led, 2–3 hours, browser-based. Each section = short concept talk
(the section page doubles as your talking track) + guided hands-on steps.
Participants who fall behind run `./solve <n-1>` and keep moving — never let
anyone stall more than 2 minutes on an environment issue.

## Run of show (150 min)

| Time | Section | Beats to land |
|---|---|---|
| 0:00–0:10 | Setup check | Everyone sees the chat UI + fallback reply |
| 0:10–0:25 | 1 Explore the bank | One Redis, four data shapes; semantic vs lexical search demo (step 5) |
| 0:25–0:50 | 2 Semantic routing | Classification as vector distance; the abstain-below-threshold moment (weather question) |
| 0:50–1:15 | 3 RAG | "The model is a reader, not a knowledge base"; the gold-loan refusal (step 6) is the compliance argument |
| 1:15–1:50 | 4 Multi-agent | Toolbox = permission model; the CUST1002 NOC refusal (step 6); a chat that mutates Redis (step 7) |
| 1:50–2:15 | 5 Agent memory | Memory is infrastructure, not prompts — the Agent Memory Server (Iris's Agent Memory) does extraction for you; the renovation → home-decor cross-sell demo (step 9) is the wow moment. Extraction is async: say the renovation line early, chat a bit, then demo the recall |
| 2:15–2:30 | 6 Semantic caching | Latency drop live on screen; the "only impersonal answers" rule; the loose-threshold failure (step 9) if time allows |
| 2:30–2:40 | 7 Wrap-up | The table mapping what they built → Redis Iris managed services |

Short on time? Cut Section 6's optional steps and Section 2 step 7, not
Section 5 step 9 — the cross-sell demo is the customer's own use case
paying off.

## Demo personas

- **Ananya (CUST1001)** — the golden path: one active + one closed loan
  (NOC works), two pre-approved offers (sales works).
- **Rohit (CUST1002)** — the guardrail: only an active loan (NOC correctly
  refused), balance-transfer offer.
- **Priya (CUST1003)** — closed loan, *no* offers (sales agent must be honest).
- **Arjun (CUST1004)** — new customer, KYC pending (journey agent friction).

## Things that go wrong

- **OpenAI rate limits with a shared key**: give the audience 2–3 keys and
  split by row, or raise the key's RPM ahead of time.
- **Someone's router matches everything / nothing**: they typo'd the
  threshold (0.07 vs 0.7). `ROUTER_DISTANCE_THRESHOLD` in `.env` wins over
  code edits.
- **`docker compose restart api` forgotten**: the #1 "my solution doesn't
  work". The pipeline is built at startup; say it once per section.
- **State weirdness after experiments**: `FLUSHALL` + restart api reseeds
  in ~30s. Cached replies survive FLUSHALL only in participants' minds.
  (`FLUSHALL` also wipes the memory server's data — it shares the same
  Redis; restart `agent-memory` too if it acts confused.)
- **Section 5 recall "doesn't work"**: 90% of the time it's the async
  extraction — the fact isn't searchable the instant the message is sent.
  Demo something else for 20 seconds, then search again.
- **Corporate proxies**: `OPENAI_BASE_URL` in `.env`; test it before the day.

## Solution snapshots

`solutions/python/<n>/` is the full state of all five exercise files *after*
section n. `./solve n` copies them over `code/python/src/` and restarts the
api. `./solve reset` restores the starter. Diff any two snapshots to see
exactly what a section adds:

```bash
diff -r solutions/python/3/src solutions/python/4/src
```

## Adapting to the customer

The bank scenario (journeys, products, tools) lives in three places only:

- `data/` — customers, loans, offers, and the loan documents
- `src/agents/personas.py` + `src/agents/tools.py` — the team and its powers
- `src/router/semantic_router.py` — the journeys (solution snapshot)

Swap those and the same workshop teaches the same Redis stack on any
domain — insurance claims, telco plans, e-commerce returns.
