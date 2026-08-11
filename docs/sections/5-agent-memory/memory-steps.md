## Steps

1. **Reproduce the amnesia.** As Ananya, ask *"what loans do I have?"* then
   *"what's the outstanding on the first one?"*. The second answer ignores
   the first exchange entirely.

2. **Meet the memory server.** It's already running as the `agent-memory`
   container:

   ```bash
   curl http://localhost:8088/v1/health
   ```

   From inside the pipeline it's reached at `http://agent-memory:8000`
   (`AGENT_MEMORY_URL` in `src/config.py`).

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
   messages, and injects `memories` into every agent's system prompt.)

8. **Restart and re-run step 1.** `docker compose restart api`. The
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
   curl -s -X POST http://localhost:8088/v1/long-term-memory/search \
     -H 'Content-Type: application/json' \
     -d '{"text": "renovation", "user_id": {"eq": "CUST1001"}, "limit": 5}'
   ```

10. **Verify isolation.** Switch to Rohit (CUST1002) and ask the same
    "extra funds" question — no renovation memory surfaces. The `user_id`
    filter is the privacy boundary.
