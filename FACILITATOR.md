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
| 0:45–1:15 | 3 RAG | First write-the-code exercises: the three retrieval modes (vector, keyword, hybrid). "The model is a reader, not a knowledge base"; the gold-loan refusal (step 5) is the compliance argument. Keyword + hybrid (steps 7–11) race all three modes — run them if the room is fast, else assign as homework; the eNACH-vs-paraphrase races (steps 9–11) make the strongest live demo |
| 1:15–1:55 | 4 Context Retriever | Attendees create an admin key on the console's **Admin keys** page and paste it into `.env` (step 3, ~3 min — the only console touch; everything else is the Python client). Beats: RAG can't answer "what's MY outstanding?" — documents vs entities (step 2), index-the-model in `ContextModel` classes (step 4, fill-in-the-kwarg TODOs — the deploy names any missed ones), build the context surface — the three client calls ship commented out, attendees uncomment and read them (step 5), run the deploy → generated tools (step 6), "look at what you didn't write" (step 7), identity injection + scoped agent keys (step 9) |
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

## Pre-workshop email to participants

Send this checklist at least two days before; items 2 and 3 are the ones
people fail to do on the day.

1. **A laptop with Docker Desktop** (or Docker Engine + Compose v2) and
   **git** installed. Verify with `docker compose version`.
2. **A free Redis Cloud account with a free database** — sign up at
   <https://cloud.redis.io/>, then **Databases → New database → Free**
   (30MB tier is enough). Keep the login: the workshop returns to the
   console to provision Context Retriever (Section 4), Agent Memory
   (Section 5), and LangCache (Section 6). Note the database's **public
   endpoint** and **default-user password** — they go into `.env` at
   setup.
3. **An OpenAI API key** (LLM + embeddings), unless the facilitator is
   handing out shared keys on the day.
4. **A network that allows outbound HTTPS** to `api.openai.com` and
   `cloud.redis.io` / `*.redis.io`, **and outbound TCP to your cloud
   database's port** (a five-digit port like `16279`, not 443 —
   corporate networks and strict VPNs often block it; test with
   `redis-cli -u <your-REDIS_URL> ping` or plan to hotspot).
5. **Free local ports**: 80 (workbench), 3000, 3001, 8000, 8088, 5540.
6. A modern browser (Chrome/Edge/Firefox). No Python or IDE setup — the
   workshop runs everything in containers, with VS Code and a terminal
   in the browser. Exercises are copy-paste / uncomment level; basic
   Python reading fluency is enough.

## Things that go wrong

- **No Redis Cloud accounts on the day**: Sections 4 (Context Retriever —
  required), 5 (managed tour), and 6 (LangCache — required) provision
  cloud services. Put "create a free Redis Cloud account + free database"
  in the pre-workshop email (it's Step 1 of Getting started), and keep
  one shared set of service credentials on a slide as the fallback for
  anyone stuck at signup.
- **Section 4 LIVE-VERIFIED (2026-08-13)** on a real account and cloud
  DB: admin key from the console's **Admin keys** page → surface with
  embedded `data_source` → 11 records imported → 15 generated tools →
  servicing / sales / NOC journeys and the identity boundary all pass
  through the graph. Contract facts learned live (don't re-learn):
  the admin API authenticates with `X-API-Key`; surface creation must
  embed the database connection under `data_source.connection_config`;
  **key-component fields must not carry an index** (the API rejects
  them — that's why Offer keys on a synthetic `offer_id` while
  customer_id/product stay plain tags); generated tools name their
  customer argument generically (`value` on filter tools, `id` on
  get_customer_by_id), so retriever.py aliases those to `customer_id`
  to keep the identity injection real; unscoped `count_*` tools are
  excluded from the agents' toolbox (a global count once answered
  "do I have offers?").
- **Section 6 LangCache LIVE-VERIFIED (2026-08-14)** against a real
  cloud service: store → semantic search hit (~400 ms round trip) →
  per-entry delete (`DELETE /entries/{id}`; note the flush-all form
  requires non-blank `attributes`). Still deserving one live pass:
  Section 5's *managed* Agent Memory service (the "Go managed" steps —
  the OSS container path is verified).
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
  for `Chat pipeline ready` or a traceback from their edit. `.env` is
  the same: it's visible at the Code panel's workspace root and the api
  reloads when it's saved. If REDIS_URL or the OpenAI key change after
  boot, restart the memory server (`docker compose restart agent-memory
  agent-memory-worker` — it re-reads `.env` on restart). One footgun:
  `sed -i`/vim-style atomic rewrites of `.env` from the Terminal can
  break its VS Code mount — use the Code panel or `nano`.
- **Keys on screen**: `.env` (with API keys) is now editable in the Code
  panel — presenters sharing their screen should keep it closed after
  editing.
- **`.env` loses lines after a Code-panel save**: seen twice in testing —
  the file ends mid-value (a truncated key) and the api goes degraded or
  a key "disappears". Check the last line of `.env` is complete after
  saving; VS Code's Timeline view (local history) holds the previous
  content for recovery, and `nano /workshop/.env` in the Terminal is the
  safe editor.
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
