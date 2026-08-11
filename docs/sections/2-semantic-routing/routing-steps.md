## Steps

1. **Open the exercise file** `code/python/src/router/semantic_router.py`.
   The five journeys are described in the module docstring; `ROUTES` is
   empty and `build_router` returns `None`.

2. **Define the five routes.** Under the `SECTION 2` banner, fill `ROUTES`
   with a `Route` per journey — `servicing`, `loan_docs`, `noc`, `sales`,
   `journey` — each with 5–7 reference utterances a real customer would
   type, and `distance_threshold=config.ROUTER_DISTANCE_THRESHOLD`. For
   example:

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

3. **Build the router.** Replace the `return None` stub in `build_router`:

   ```python
   return SemanticRouter(
       name=config.ROUTER_NAME,
       vectorizer=get_vectorizer(),
       routes=ROUTES,
       redis_url=redis_url,
       overwrite=True,
       # Route on the single nearest reference. The default averages the
       # distances of every matched reference per route, which dilutes an
       # (almost) exact match with the route's unrelated references.
       routing_config=RoutingConfig(aggregation_method="min", max_k=1),
   )
   ```

   That `routing_config` is worth a pause: aggregation strategy is a real
   design decision in semantic routing. *Nearest reference wins* (`min`)
   rewards routes for their best match; *average* rewards routes whose
   references all cluster near the message. For journeys defined by a few
   sharp example utterances, `min` is what you want.

4. **Wire it into the pipeline.** In `code/python/src/chat/service.py`,
   under the `SECTION 2 - SEMANTIC ROUTING` banner, replace:

   ```python
   route = None
   ```

   with:

   ```python
   route = route_message(self.router, request.message)
   ```

   and under the `SECTION 3 - RAG / SECTION 4 - MULTI-AGENT` banner, make the
   reply *show* the routing while the agents are still stubs — replace the
   fallback line with:

   ```python
   reply, agent, citations = (self._canned_reply(route),
                              route or "fallback", [])
   ```

5. **Save and test.** The api reloads automatically when files change (uvicorn `--reload`; a second or two), then in the **App** panel:

   - *"when is my next EMI due?"* → routed to **servicing**
   - *"how much to close my loan early?"* → **loan_docs**
   - *"where is my closure certificate?"* → **noc** — no keyword "NOC" needed
   - *"what's the weather in Mumbai?"* → no route → fallback

   Watch the **route chip** under each reply and the pipeline inspector.

6. **Peek behind the curtain.** In the Redis Insight panel:

   ```bash
   FT.SEARCH wa-journey-router "*" LIMIT 0 30 RETURN 2 reference route_name
   ```

   Your reference utterances, embedded and indexed — the entire "model" of
   this classifier. Adding a journey is appending a `Route`, not retraining.

7. **(Optional) Tune the threshold.** Set `ROUTER_DISTANCE_THRESHOLD=0.5` in
   `.env` and `docker compose restart api` from the host (env changes need a
   restart; stricter → more fallbacks), then put
   it back. This threshold-tuning trade-off returns in Section 6.
