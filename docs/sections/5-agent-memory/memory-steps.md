## Steps

1. **Reproduce the amnesia.** As Ananya, ask *"what loans do I have?"* then
   *"what's the outstanding on the first one?"*. The second answer ignores
   the first exchange entirely.

2. **Provision Agent Memory.** In the [Redis Cloud
   console](https://cloud.redis.io/), select **Agent Memory** from the
   left-hand menu, then **Quick create** (it uses — or creates — your free
   database). Copy the **service API key** when it appears — *it is shown
   only once*. Then open the service's **Configuration** tab and copy the
   **Endpoint** and **Store ID**.

3. **Configure the app.** In the **Code** panel, fill the three keys in
   `.env` (the api reloads on save):

   ```bash
   AGENT_MEMORY_URL=<ENDPOINT>          # include https://
   AGENT_MEMORY_STORE_ID=<STORE_ID>
   AGENT_MEMORY_API_KEY=<API_KEY>
   ```

   Until these are set, the memory client is a no-op — the api log shows
   the warning `Agent Memory is not configured` at startup; after the
   save, it's gone.

4. **Read the provided plumbing.** Open
   `code/python/src/memory/redis_memory.py`. The `AgentMemory` class
   already carries the authenticated `httpx` client (Bearer key,
   store-scoped base URL) and a provided `session_history` — short-term
   memory is just reading the event log back. The pipeline call-sites in
   `service.py` are wired too. What's missing are the two payloads: what
   to *write*, and what to *search*.

5. **Exercise — remember the turn.** In `remember_turn`, fill in the two
   event payloads under the `SECTION 5` banner:

   ```python
   user_event = {
       "actorId": customer_id,
       "role": "USER",
       "content": [{"text": user_message}],
   }
   bot_event = {
       "actorId": BOT_ACTOR_ID,
       "role": "ASSISTANT",
       "content": [{"text": reply}],
   }
   ```

   Two events per turn, posted to `session-memory/events`. The first
   event's `actorId` becomes the session's owner — the extraction files
   every fact under this customer.

6. **Exercise — recall.** In `recall`, fill in the semantic-search
   payload:

   ```python
   payload = {
       "text": query,
       "filter": {"ownerId": {"eq": customer_id}},
       "limit": k,
   }
   ```

   That's the entire long-term memory implementation — the extraction
   happened server-side, on its own.

7. **Save and re-run step 1.** The api reloads on save; the follow-up now
   resolves "the first one" from session memory. Click **⟳ new chat** — a
   fresh `sessionId` starts blank, as it should.

8. **See the cross-sell payoff.** As Ananya: say *"We are redoing our home
   interiors this year, modular kitchen and wardrobes"*. Give the service
   **a minute or two** — extraction runs on a background cadence, plus an
   LLM call — then click **⟳ new chat** (fresh session, session memory
   gone) and ask *"I need some extra funds, what are my options?"*. The
   sales agent leads with the **home decor loan**: long-term memory
   recalled the renovation across sessions. See what was extracted — in
   the **Terminal** panel (paste your own three values):

   ```bash
   curl -s -X POST \
     -H "Authorization: Bearer <API_KEY>" -H 'Content-Type: application/json' \
     "<ENDPOINT>/v1/stores/<STORE_ID>/long-term-memory/search" \
     -d '{"text": "renovation plans",
          "filter": {"ownerId": {"eq": "CUST1001"}},
          "limit": 5}' | jq
   ```

9. **Verify isolation.** Switch to Rohit (CUST1002) and ask the same
   "extra funds" question — no renovation memory surfaces. The `ownerId`
   filter is the privacy boundary.

10. **(Optional) Tour the production controls.** In the service's
    **Configuration** tab: per-tier TTLs, extraction cadence, automatic
    session summarization (long sessions collapse into a summary event),
    custom memory types, and sensitive-data exclusions — the knobs you'd
    otherwise be building and operating yourself. The full API surface is
    in the [Agent Memory API
    reference](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/api-reference).
