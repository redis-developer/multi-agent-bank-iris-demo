## Steps

> This section is a **code walkthrough** — the router ships already built.
> Nothing to write; the goal is that by step 4 you could add a sixth
> journey yourself.

1. **Open the provided file** `src/router/semantic_router.py` in the
   **Code** panel and start with `ROUTES`. Five `Route` objects, one per
   journey — and notice what each one is: just a name, a handful of
   reference utterances a real customer would type, and a distance
   threshold. No training data, no model, no rules. For example:

   ```python
   Route(
       name="noc",
       references=[
           "I need an NOC for my closed loan",
           "send me my loan closure certificate",
           "issue a no objection certificate",
           "my loan is closed but the bureau still shows it active",
       ],
       distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
   ),
   ```

2. **Read `build_router`.** Three things worth noticing:

   - the `vectorizer` — the same embedding model used everywhere else in
     this workshop turns each reference into a vector, stored in Redis
     under the router's own index (`overwrite=True` rebuilds it at boot);
   - `distance_threshold` — the honesty knob from the concept page;
   - `routing_config=RoutingConfig(aggregation_method="min", max_k=1)` —
     *nearest reference wins*. This is a real design decision: the
     default (`avg`) scores a route by the average distance of all its
     matched references, which dilutes an almost-exact match with the
     route's unrelated references. For journeys defined by a few sharp
     examples, `min` is what you want.

3. **Read `route_message`.** One embedding lookup, and one honest path:
   if no reference is within the threshold, it returns `None` — the
   router *abstains* instead of guessing. In Section 4 the supervisor
   uses an LLM as the fallback classifier for exactly those messages, so
   LLM judgment is spent only where the cheap path gave up.

4. **Find the call-site.** In `src/chat/service.py`, `chat()` runs

   ```python
   route = route_message(self.router, request.message)
   ```

   on every message, before anything else spends a token. The reply is
   still canned per journey (the agents arrive in Sections 3–4) — which
   makes routing easy to *see* in the next step.

5. **Test it in the App panel:**

   - *"when is my next EMI due?"* → routed to **servicing**
   - *"how much to close my loan early?"* → **loan_docs**
   - *"where is my closure certificate?"* → **noc** — no keyword "NOC"
     needed; that's matching on meaning
   - *"what's the weather in Mumbai?"* → no route → fallback (the abstain
     path from step 3)

   Watch the **route chip** under each reply and the pipeline inspector.

6. **Peek behind the curtain.** In the Redis Insight panel:

   ```bash
   FT.SEARCH wa-journey-router "*" LIMIT 0 30 RETURN 2 reference route_name
   ```

   The reference utterances, embedded and indexed — that is the *entire*
   "model" of this classifier. Adding a sixth journey is appending a
   `Route` and restarting, not retraining anything.

7. **(Optional) Tune the threshold.** Set `ROUTER_DISTANCE_THRESHOLD=0.5`
   in `.env` (open it in the **Code** panel at the workspace root and
   save — the api reloads on it; stricter → more fallbacks), then put
   it back. This
   threshold-tuning trade-off returns in Section 6.
