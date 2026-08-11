## Steps

1. **Reproduce the amnesia.** As Ananya, ask *"what loans do I have?"* then
   *"what's the outstanding on the first one?"*. The second answer ignores
   the first exchange entirely.

2. **Meet the memory server.** It's already running as the `agent-memory`
   container. In the **Terminal** panel:

   ```bash
   curl http://agent-memory:8000/v1/health
   ```

   That hostname is how the pipeline reaches it too (`AGENT_MEMORY_URL`
   in `src/config.py`).

3. **Open the exercise file** `code/python/src/memory/redis_memory.py`.
   The `AgentMemory` class already holds an `httpx` client pointed at the
   server — the three methods are stubs.

4. **Working memory: read the session.** Implement `session_history`:

   ```python
   response = self.http.get(
       f"/v1/working-memory/{session_id}",
       params={"recent_messages_limit": limit},
   )
   if response.status_code == 404:
       return []  # first turn of a new session
   response.raise_for_status()
   return [{"role": m["role"], "content": m["content"]}
           for m in response.json().get("messages", [])]
   ```

5. **Working memory: write the turn.** Implement `remember_turn`:

   ```python
   messages = self.session_history(session_id, limit=50)
   messages += [
       {"role": "user", "content": user_message},
       {"role": "assistant", "content": reply},
   ]
   self.http.put(
       f"/v1/working-memory/{session_id}",
       json={"messages": messages, "user_id": customer_id},
   ).raise_for_status()
   ```

   The `user_id` matters: it's what lets the server file extracted facts
   under this customer.

6. **Long-term memory: search.** Implement `recall` — the whole thing is
   one request:

   ```python
   response = self.http.post(
       "/v1/long-term-memory/search",
       json={
           "text": query,
           "user_id": {"eq": customer_id},
           "limit": k,
       },
   )
   response.raise_for_status()
   return [m["text"] for m in response.json().get("memories", [])]
   ```

   Notice there is no extraction code anywhere — the server does that on
   its own as working memory arrives.

7. **Wire the pipeline call-sites.** In `src/chat/service.py`, under the
   *recall this customer's context* banner, replace the two stub lines with:

   ```python
   history = self.memory.session_history(request.session_id)
   memories = self.memory.recall(request.customer_id, request.message)
   ```

   and under the *remember this turn* banner add:

   ```python
   self.memory.remember_turn(request.session_id, request.customer_id,
                             request.message, reply)
   ```

   (`_run_graph` already accepts `history` and prepends it to the graph's
   messages, and the graph injects `memories` as a note next to the latest
   message — see `_messages_with_memories` in `src/agents/graph.py`.)

8. **Save and re-run step 1.** The api reloads on save; the
   follow-up now resolves "the first one" from working memory. Click
   **⟳ new chat** — a fresh `session_id` starts blank, as it should.

9. **See the cross-sell payoff.** As Ananya: say *"We are redoing our home
   interiors this year, modular kitchen and wardrobes"*. Give the server
   **about a minute** — extraction is a background job with a trailing
   debounce, plus an LLM call — then click **⟳ new chat** (fresh session,
   working memory gone) and ask *"I need some extra funds, what are my
   options?"*. The sales agent leads with the **home decor loan**:
   long-term memory recalled the renovation across sessions. See what the
   server extracted:

   ```bash
   curl -s -X POST http://agent-memory:8000/v1/long-term-memory/search \
     -H 'Content-Type: application/json' \
     -d '{"text": "renovation", "user_id": {"eq": "CUST1001"}, "limit": 5}'
   ```

   (run it in the Terminal panel)

10. **Verify isolation.** Switch to Rohit (CUST1002) and ask the same
    "extra funds" question — no renovation memory surfaces. The `user_id`
    filter is the privacy boundary.

---

### Go managed: Agent Memory on Redis Cloud

Everything above ran against the self-hosted Agent Memory Server container.
The same component is a **managed service on Redis Cloud** — with extras
the container doesn't give you: configurable TTLs per memory tier,
extraction cadence, automatic session summarization, custom memory types,
and sensitive-data exclusions. Provision one now and take it for a spin
(you need a [Redis Cloud](https://cloud.redis.io/) account; free tier is
enough).

11. **Create the service.** In the [Redis Cloud
    console](https://cloud.redis.io/), select **Agent Memory** from the
    left-hand menu, then **Quick create** (it uses — or creates — your free
    database). Copy the **service API key** when it appears — *it is shown
    only once*. Then open the service's **Configuration** tab and copy the
    **Endpoint** and **Store ID**.

12. **Set up the Terminal panel** and check the service:

    ```bash
    export AGENT_MEMORY_CLOUD='<ENDPOINT>'   # include https://
    export STORE_ID='<STORE_ID>'
    export API_KEY='<API_KEY>'

    curl -s -H "Authorization: Bearer $API_KEY" "$AGENT_MEMORY_CLOUD/health" | jq
    ```

13. **Replay the bank scenario against the cloud.** Add Ananya's renovation
    message as a session event:

    ```bash
    curl -s -X POST \
      -H "Authorization: Bearer $API_KEY" -H 'Content-Type: application/json' \
      "$AGENT_MEMORY_CLOUD/v1/stores/$STORE_ID/session-memory/events" \
      -d "{\"sessionId\": \"bank-demo\", \"actorId\": \"CUST1001\",
           \"role\": \"USER\",
           \"content\": [{\"text\": \"We are redoing our home interiors this year, modular kitchen and wardrobes\"}],
           \"createdAt\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\"}" | jq
    ```

14. **Search the extracted memory** (give the extraction cadence a minute
    or two, then):

    ```bash
    curl -s -X POST \
      -H "Authorization: Bearer $API_KEY" -H 'Content-Type: application/json' \
      "$AGENT_MEMORY_CLOUD/v1/stores/$STORE_ID/long-term-memory/search" \
      -d '{"text": "renovation plans",
           "filter": {"ownerId": {"eq": "CUST1001"}},
           "limit": 5}' | jq
    ```

    Same two-tier model you just built against, productised: sessions are
    store-scoped (`/v1/stores/{storeId}/…`) and long-term memories filter
    by `ownerId` — the managed counterpart of the `user_id` privacy
    boundary from step 10. Swapping the app over is re-implementing
    `AgentMemory`'s three methods against these endpoints — see the
    [Agent Memory API reference](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/api-reference).
