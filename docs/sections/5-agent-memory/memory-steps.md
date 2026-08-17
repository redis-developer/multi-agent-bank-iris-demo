## Steps

1. **Reproduce the amnesia.** As Ananya, ask *"what loans do I have?"* then
   *"what's the outstanding on the first one?"*. The second answer ignores
   the first exchange entirely.

2. **Exercise 1 — create the service and set the extraction strategy.**
   In the [Redis Cloud console](https://cloud.redis.io/), select **Agent
   Memory** from the left-hand menu, then **Create custom service** (not
   Quick create — the strategy is the point). Enter a service name, select
   your database and its `default` user, and under **Memory
   configuration** set:

   | Setting | Value | What it controls |
   |:--------|:------|:-----------------|
   | **Short-term TTL** | `1` day | How long session memory is retained. |
   | **Long-term TTL** | `365` days | How long extracted memories are retained. |
   | **Extraction cadence** | `1` minute | How often session events are processed for extraction. One minute is for this workshop — recall works moments after you say something; use a longer interval in production. |
   | **Automatic summarization** | Disabled | Whether older session events are condensed into a summary. Off for the workshop, so the session log stays verbatim. |

   Select **Create**. Copy the **service API key** when it appears — *it
   is shown only once*. Then open the service's **Configuration** tab and
   copy the **Endpoint** and **Store ID**.

   This screen *is* the long-term memory strategy: what gets remembered,
   for how long, and how quickly it becomes recallable — configured on the
   service, not coded in your app.

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
   store-scoped base URL), a provided `session_history` (short-term memory
   is just reading the event log back), and a provided `recall` — the
   entire long-term implementation is one `ownerId`-filtered semantic
   search, because the extraction you configured in step 2 fills long-term
   memory on its own. The pipeline call-sites in `service.py` are wired
   too.

5. **Exercise 2 — create session memory.** In `remember_turn`, under the
   `SECTION 5` banner, uncomment the parameters of the two event payloads:

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
   event's `actorId` becomes the session's owner — extraction files every
   fact under this customer.

6. **Save and re-run step 1.** The api reloads on save; the follow-up now
   resolves "the first one" from session memory. Click **⟳ new chat** — a
   fresh `sessionId` starts blank, as it should.

7. **See the cross-sell payoff.** As Ananya: say *"We are redoing our home
   interiors this year, modular kitchen and wardrobes"*. Wait **about a
   minute** — the extraction cadence you set in step 2 — then click
   **⟳ new chat** (fresh session, session memory gone) and ask *"I need
   some extra funds, what are my options?"*. The sales agent leads with
   the **home decor loan**: long-term memory recalled the renovation
   across sessions — a fact nobody's code wrote, extracted by the
   service on its own.

8. **Verify isolation.** Switch to Rohit (CUST1002) and ask the same
   "extra funds" question — no renovation memory surfaces. The `ownerId`
   filter is the privacy boundary.

9. **(Optional) Push the strategy further.** Back on the service's
   **Configuration** tab: automatic summarization (long sessions collapse
   into a summary event), **custom memory types** (a `loan_preference`
   type with structured fields your extraction fills), and
   **sensitive-data exclusions** (an extraction prompt that keeps OTPs and
   card numbers out of long-term memory) — the rest of the strategy
   surface, all configuration, no code. The full API is in the
   [Agent Memory API
   reference](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/api-reference).
