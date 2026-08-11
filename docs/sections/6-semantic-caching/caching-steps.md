## Steps

> This section provisions a real cloud service. You need a
> [Redis Cloud](https://cloud.redis.io/) account (the free tier is enough).

1. **Create a LangCache service.** In the [Redis Cloud
   console](https://cloud.redis.io/), select **LangCache** from the
   left-hand menu, then **Quick create** (it will use — or create — your
   free database). When the service is created, a window shows your
   **service API key**: copy it now — *it is shown only once*. Then open
   the service's **Configuration** tab and copy the **Cache ID** and the
   **endpoint URL**.

2. **Give the bot its cache.** Put the three values into `.env` (from the
   host machine):

   ```bash
   LANGCACHE_URL=https://<your-endpoint-host>
   LANGCACHE_CACHE_ID=<your-cache-id>
   LANGCACHE_API_KEY=<your-service-key>
   ```

   then `docker compose restart api` (env changes need a restart). Until
   these are set, the api logs a warning and simply skips caching.

3. **Open the exercise file** `code/python/src/cache/semantic_cache.py`.
   The provided `__init__` already builds an authenticated httpx client
   pointed at `/v1/caches/{cacheId}` — the two methods are stubs.

4. **Implement `check`** — the *search* half of cache-aside:

   ```python
   if not self.configured:
       return None
   response = self.http.post("/entries/search", json={
       "prompt": message,
       "similarityThreshold": config.CACHE_SIMILARITY_THRESHOLD,
   })
   response.raise_for_status()
   return _cached_response(response.json())
   ```

   LangCache embeds the prompt server-side and runs the similarity search
   inside the service — no OpenAI call happens on this path at all.

5. **Implement `store`** — the other half:

   ```python
   if not self.configured:
       return None
   self.http.post("/entries", json={
       "prompt": message,
       "response": reply,
   }).raise_for_status()
   ```

6. **Save and measure.** In the **App** panel ask:

   > What is the foreclosure charge on a personal loan?

   Note the latency in the inspector — a full RAG round trip, seconds. Now
   ask the *paraphrase*:

   > what foreclosure charges apply if I close my personal loan early?

   **⚡ cache hit** — the same answer in one HTTPS round trip, zero LLM
   tokens, zero embedding calls from your app. The route chip reads
   `cache`: the router, graph, and LLM never ran.

7. **Verify the personal-data rule.** Ask *"what's my outstanding
   balance?"* twice. Never cached — it runs the servicing agent both
   times, because only `loan_docs` replies are stored. That rule is one
   `if` in `service.py`; find it and convince yourself it's load-bearing.

8. **Inspect the cache from the Terminal panel** — the same API your app
   calls:

   ```bash
   curl -s -X POST "$LANGCACHE_URL/v1/caches/$LANGCACHE_CACHE_ID/entries/search" \
     -H "Authorization: Bearer $LANGCACHE_API_KEY" \
     -H 'Content-Type: application/json' \
     -d '{"prompt": "foreclosure charges?"}' | jq
   ```

   (export the three values in the terminal first). The Redis Cloud
   console's LangCache page also shows entries and hit-rate metrics.

9. **(Optional) Break it on purpose.** Set
   `CACHE_SIMILARITY_THRESHOLD=0.5` in `.env`, restart, and ask *"what is
   the processing fee on a personal loan?"* — at 0.5, this related-but-
   different question can serve the cached *foreclosure* answer, right or
   not. Put it back to `0.85`. That experiment is the whole operational
   story of semantic caching in one minute.
