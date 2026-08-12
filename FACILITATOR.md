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
| 0:10–0:25 | 1 Explore the bank | Their cloud DB + the FAQ index; semantic vs lexical (step 4); the empty-bank teaser (step 5) pays off in Section 4 |
| 0:25–0:45 | 2 Semantic routing | Observe-the-code section (no typing): read routes → thresholds → min-aggregation, then test live; the abstain-below-threshold moment (weather question) |
| 0:45–1:15 | 3 RAG | First write-the-code exercise. "The model is a reader, not a knowledge base"; the gold-loan refusal (step 6) is the compliance argument. *Going deeper* (steps 8–14): build keyword + hybrid search and race all three modes — run it if the room is fast, else assign as homework; the eNACH-vs-paraphrase races (steps 10–12) make the strongest live demo |
| 1:15–1:55 | 4 Context Retriever | Attendees provision the real service on Redis Cloud (step 3, ~5 min). Beats: the agents *starve* without a data layer (step 2), model-the-bank in `ContextModel` classes (step 4), one deploy call → surface + agent key + data import + generated tools (step 5), "look at what you didn't write" (step 6), identity injection + scoped agent keys (step 8) |
| 1:50–2:15 | 5 Agent memory | Memory is infrastructure, not prompts — the Agent Memory Server (Iris's Agent Memory) does extraction for you; the renovation → home-decor cross-sell demo (step 9) is the wow moment. Extraction is async: say the renovation line early, chat a bit, then demo the recall. "Go managed" (steps 11–14): provision the Redis Cloud service + curl tour — run it if accounts are ready, else homework |
| 2:15–2:35 | 6 LangCache | Attendees provision a real cloud service (steps 1–2, ~5 min) — have Redis Cloud accounts created BEFORE the day. Latency drop live on screen; "no vectorizer, no schema, no index" is the beat; the "only impersonal answers" rule; the loose-threshold failure (step 9) if time allows |
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

- **No Redis Cloud accounts on the day**: Sections 4 (Context Retriever —
  required), 5 (managed tour), and 6 (LangCache — required) provision
  cloud services. Put "create a free Redis Cloud account + free database"
  in the pre-workshop email (it's Step 0 of Getting started), and keep
  one shared set of service credentials on a slide as the fallback for
  anyone stuck at signup.
- **VERIFY BEFORE THE DAY — the cloud path end to end**: run Step 0 +
  Sections 1 and 4 once against a real Redis Cloud database and Context
  Retriever service. Three things to confirm: the client integration
  (deploy + generated tool names + MCP calls — built against
  `redis-context-retriever` 0.0.6, mock-tested only), the storage format
  of imported records (the NOC action tool reads them; it tolerates JSON
  and hash), and the cloud DB's Redis version — Section 3's *hybrid*
  exercise needs FT.HYBRID (Redis 8.4+); if the free tier is older, demo
  hybrid on the local fallback container or skip step 9's hybrid race.
- **Service keys are shown once**: both Agent Memory and LangCache display
  the API key only at creation. Say it out loud before anyone clicks
  Create; regenerating from the service page is the recovery.
- **OpenAI rate limits with a shared key**: give the audience 2–3 keys and
  split by row, or raise the key's RPM ahead of time.
- **Someone's router matches everything / nothing**: they typo'd the
  threshold (0.07 vs 0.7). `ROUTER_DISTANCE_THRESHOLD` in `.env` wins over
  code edits.
- **"My solution doesn't work"**: the api auto-reloads on save (uvicorn
  --reload rebuilds the whole pipeline) — check `docker compose logs api`
  for `Chat pipeline ready` or a traceback from their edit. Only `.env`
  changes need a manual step — and it must be `docker compose up -d api`
  (recreate): a plain `restart` does NOT re-read `.env`. This is the #2
  "my config change did nothing".
- **State weirdness after experiments**: `FLUSHALL` + restart api reseeds
  the FAQs in ~30s — but it runs against the attendee's *cloud* DB, so it
  also wipes Section 4's imported records (re-run the deploy) and the
  memory server's data (restart `agent-memory` too). LangCache entries
  live in their own service and survive — clear them from the console.
- **Section 5 recall "doesn't work"**: 90% of the time it's the async
  extraction — the fact isn't searchable the instant the message is sent.
  Demo something else for 20 seconds, then search again.
- **Corporate proxies**: `OPENAI_BASE_URL` in `.env`; test it before the day.

## Solution snapshots

`solutions/python/<n>/` (n = 3–6) is the full state of the exercise files
*after* section n; sections 1 and 2 change no code, and the semantic router
ships already solved in the starter. `./solve n` copies a snapshot over
`code/python/src/` (the api auto-reloads). `./solve reset` restores the
starter. Diff any two snapshots to see exactly what a section adds:

```bash
diff -r solutions/python/3/src solutions/python/4/src
```

## Adapting to the customer

The bank scenario (journeys, products, tools) lives in three places only:

- `data/` — customers, loans, offers, and the loan documents
- `src/agents/personas.py` + `src/agents/tools.py` — the team and its powers
- `src/router/semantic_router.py` — the journeys (provided file)

Swap those and the same workshop teaches the same Redis stack on any
domain — insurance claims, telco plans, e-commerce returns.
