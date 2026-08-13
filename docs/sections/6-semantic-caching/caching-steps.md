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

2. **Give the bot its cache.** In the **Code** panel, open `.env`
   (workspace root), add the three values, and save:

   ```bash
   LANGCACHE_URL=https://<your-endpoint-host>
   LANGCACHE_CACHE_ID=<your-cache-id>
   LANGCACHE_API_KEY=<your-service-key>
   ```

   The api watches `.env` and reloads within a few seconds of the save.
   Until these are set, it logs a warning and simply skips caching.

3. **Open the exercise file** `src/cache/semantic_cache.py`. The
   provided `__init__` already builds an authenticated httpx client
   pointed at `/v1/caches/{cacheId}` — the two methods are stubs with
   their solutions written inside, commented out.

4. **Exercise — bring `check` to life** (the *search* half of
   cache-aside): select the commented block inside `check`, press
   `Cmd+/` (`Ctrl+/` on Windows/Linux), save. Read what you enabled —
   one POST to `/entries/search` with two parameters:

   - `prompt` — the customer's message, as typed
   - `similarityThreshold` — `config.CACHE_SIMILARITY_THRESHOLD`
     (0.85): how close a paraphrase must be to count as "the same
     question"

   LangCache embeds the prompt server-side and runs the similarity search
   inside the service — no OpenAI call happens on this path at all.

5. **Exercise — bring `store` to life**: same drill inside `store`. One
   POST to `/entries` with the pair the cache will serve later:
   `prompt` (the question) and `response` (the generated reply).

6. **Wire the pipeline to the cache.** Open `src/chat/service.py` —
   two `SECTION 6` banners in `chat()`:

   - Under *check the cache before any work*, replace the `None`:

     ```python
     cached_reply = self.cache.check(request.message)
     ```

   - Under *store shareable replies*, uncomment the two code lines:

     ```python
     if agent == "loan_docs":
         self.cache.store(request.message, reply)
     ```

   That `if` is the privacy rule: only the loan-docs agent's answers are
   impersonal enough to share across customers.

7. **Save and measure.** In the **App** panel ask:

   > What is the foreclosure charge on a personal loan?

   Note the latency in the inspector — a full RAG round trip, seconds. Now
   ask the *paraphrase*:

   > what foreclosure charges apply if I close my personal loan early?

   **⚡ cache hit** — the same answer in one HTTPS round trip, zero LLM
   tokens, zero embedding calls from your app. The route chip reads
   `cache`: the router, graph, and LLM never ran.

8. **Verify the personal-data rule.** Ask *"what's my outstanding
   balance?"* twice. Never cached — it runs the servicing agent both
   times, because of the one `if` you uncommented in step 6. Convince
   yourself it's load-bearing: without it, one customer's balance could
   become another customer's cache hit.

9. **Inspect the cache from the Terminal panel** — the same API your app
   calls:

   ```bash
   curl -s -X POST "$LANGCACHE_URL/v1/caches/$LANGCACHE_CACHE_ID/entries/search" \
     -H "Authorization: Bearer $LANGCACHE_API_KEY" \
     -H 'Content-Type: application/json' \
     -d '{"prompt": "foreclosure charges?"}' | jq
   ```

   (export the three values in the terminal first). The Redis Cloud
   console's LangCache page also shows entries and hit-rate metrics.

10. **(Optional) Break it on purpose.** Set
   `CACHE_SIMILARITY_THRESHOLD=0.5` in `.env` (Code panel, save), and
   ask *"what is
   the processing fee on a personal loan?"* — at 0.5, this related-but-
   different question can serve the cached *foreclosure* answer, right or
   not. Put it back to `0.85`. That experiment is the whole operational
   story of semantic caching in one minute.
