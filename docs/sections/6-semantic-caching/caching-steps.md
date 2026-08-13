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

3. **Open the exercise file** `src/cache/semantic_cache.py`. Everything
   is wired — the authenticated httpx client (`__init__`), the two
   POSTs, the guards, and the pipeline already calls the cache on every
   message (`service.py`, two provided `SECTION 6` banners). What's
   missing is the part that matters: both request **payloads are
   empty**, and an empty payload keeps the cache path off. The moment
   you fill them, caching is live.

4. **Exercise — fill `check`'s payload** (the *search* half of
   cache-aside). Two parameters, spelled out in the banner right above
   the empty `payload = { ... }`:

   ```python
   "prompt": message,
   "similarityThreshold": config.CACHE_SIMILARITY_THRESHOLD,
   ```

   `prompt` is the customer's question as typed; the threshold (0.85
   from config) is how close a paraphrase must be to count as "the same
   question". LangCache embeds the prompt server-side and runs the
   similarity search inside the service — no OpenAI call happens on
   this path at all.

5. **Exercise — fill `store`'s payload**: the pair the cache will serve
   on the next similar question:

   ```python
   "prompt": message,
   "response": reply,
   ```

6. **Read where the pipeline calls it** — `src/chat/service.py`, both
   provided: `check` runs *before any other work* (a hit skips the
   router, the graph, and every LLM call), and `store` runs only when
   `agent == "loan_docs"` — the privacy rule: only the loan-docs
   agent's answers are impersonal enough to share across customers.

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
   times, because of the `loan_docs` guard you read at the store
   call-site (step 6). Convince yourself it's load-bearing: without it,
   one customer's balance could become another customer's cache hit.

9. **(Optional) Break it on purpose.** Set
   `CACHE_SIMILARITY_THRESHOLD=0.5` in `.env` (Code panel, save), and
   ask *"what is
   the processing fee on a personal loan?"* — at 0.5, this related-but-
   different question can serve the cached *foreclosure* answer, right or
   not. Put it back to `0.85`. That experiment is the whole operational
   story of semantic caching in one minute.
