## Steps

1. **Open the exercise file** `code/python/src/cache/semantic_cache.py`.

2. **Create the cache.** In `ReplyCache.__init__`, replace
   `self.cache = None` with:

   ```python
   self.cache = SemanticCache(
       name=config.CACHE_NAME,
       redis_url=redis_url,
       vectorizer=get_vectorizer(),
       distance_threshold=config.CACHE_DISTANCE_THRESHOLD,
   )
   ```

3. **Implement `check`** — return the stored response on a semantic hit:

   ```python
   hits = self.cache.check(prompt=message, num_results=1)
   if hits:
       return hits[0]["response"]
   return None
   ```

4. **Implement `store`:**

   ```python
   self.cache.store(prompt=message, response=reply)
   ```

5. **Wire the pipeline call-sites.** In `src/chat/service.py`, replace
   `cached_reply = None` (SECTION 6 banner) with:

   ```python
   cached_reply = self.cache.check(request.message)
   ```

   and under the *store shareable replies* banner add the policy rule —
   cache **only** the impersonal loan_docs answers:

   ```python
   if agent == "loan_docs":
       self.cache.store(request.message, reply)
   ```

6. **Save and test.** The api reloads automatically when files change (uvicorn `--reload`; a second or two), then ask:

   > What is the foreclosure charge on a personal loan?

   Note the latency in the inspector (a full RAG round trip, seconds). Now
   ask the *paraphrase*:

   > what foreclosure charges apply if I close my personal loan early?

   **⚡ cache hit** — same answer, tens of milliseconds, zero LLM tokens.
   The route chip reads `cache`: the router, graph, and LLM never ran.

7. **Verify the personal-data rule.** Ask *"what's my outstanding balance?"*
   twice. Never cached — it runs the servicing agent both times, because
   only `loan_docs` replies are stored. This rule is one `if` in
   `service.py`; find it and convince yourself it's load-bearing.

8. **Inspect the cache in Redis:**

   ```bash
   FT.SEARCH wa-reply-cache "*" LIMIT 0 5 RETURN 2 prompt response
   ```

9. **(Optional) Break it on purpose.** Set `CACHE_DISTANCE_THRESHOLD=0.5`
   in `.env`, restart, and ask *"how much does it cost to close my loan
   early?"* — at 0.5 this related-but-different question (measured distance
   ≈0.43 from the cached one) now serves the cached personal-loan answer,
   right or not. Put the threshold back to `0.25`. That experiment is the
   whole operational story of semantic caching in one minute.
