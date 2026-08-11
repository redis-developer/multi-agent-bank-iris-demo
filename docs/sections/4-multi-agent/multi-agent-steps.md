## Steps

> The multi-agent code is **provided** — this workshop's exercises focus on
> the Redis context layer, not the agent framework. Steps 1–3 are a guided
> read; step 4 is the section's only edit (one line).

1. **Meet the team.** Open `code/python/src/agents/personas.py` (provided):
   five personas, each a system prompt plus an allowed-tools list. Then skim
   `src/agents/tools.py` — every tool hits Redis: `get_customer_loans`,
   `check_noc_eligibility`, `issue_noc`, `calculate_emi`,
   `qualify_documents`, `generate_lan`, `initiate_disbursement`,
   `get_preapproved_offers`. Note that the toolbox *is* the permission
   model: only the journey agent can move money.

2. **Read the nodes** in `code/python/src/agents/graph.py` (provided):
   `make_tool_agent_node` (the think→act→observe loop — watch a tool call
   go out and a `ToolMessage` come back), `make_loan_docs_node` (Section
   3's RAG as a graph node), and `make_supervisor_node` — notice it trusts
   `state["route"]` from the Section 2 router first and only asks the LLM
   when the router abstained.

3. **Read the wiring** at the bottom of the same file: `build_agent_graph`
   is the whole org chart in ~15 lines — `START → supervisor`, a
   conditional edge to whichever agent the supervisor picked, every agent
   `→ END`. If you ever add a sixth journey, this (plus a persona and a
   route) is everything it takes.

4. **Hand the pipeline to the graph.** In `src/chat/service.py`, under the
   `SECTION 3 - RAG / SECTION 4 - MULTI-AGENT` banner, replace the Section 3
   if/else with one line:

   ```python
   reply, agent, citations = self._run_graph(request, route, memories,
                                             history)
   ```

   (`_run_graph` is provided — it packs the message, customer, route,
   memories, and session history into the graph state and invokes it.
   `history` and `memories` stay empty until Section 5 fills them.)

5. **Save and test.** The api reloads automatically when files change (uvicorn `--reload`; a second or two), then, as
   **Ananya Sharma (CUST1001)**:

   - *"what's the outstanding on my loans?"* → **servicing** reads both her
     loans from Redis: the active ₹2,38,101 and the closed one.
   - *"I need an NOC"* → **noc** finds the closed loan `LAN20220042`, checks
     eligibility, and issues an NOC with a reference number.
   - *"do I have any offers?"* → **sales** leads with her pre-approved
     top-up and quantifies the EMI.
   - *"calculate EMI for 5 lakhs at 11.5% for 4 years"* → **journey** calls
     `calculate_emi`: ₹13,044/month.

6. **Verify the guardrail.** Switch the persona dropdown to **Rohit Verma
   (CUST1002)** — his only loan is active — and ask for an NOC. The agent
   must refuse and explain: NOC needs a closed loan. That's the
   `check_noc_eligibility` tool enforcing policy, not prompt luck.

7. **See a tool write state.** Run a mini end-to-end journey: *"I accept the
   pre-approved top-up, documents are PAN and Aadhaar, generate my LAN"*,
   then confirm disbursement when asked. In the Redis Insight panel:

   ```bash
   GET counter:lan
   JSON.GET loan:LAN20260001 $
   KEYS noc:*
   ```

   The chat changed the database. The bot is now a system of record client,
   not a text generator.

8. **Exercise the fallback.** Ask something no route covers — *"I want to
   complain about the app"*. The router abstains, the supervisor's LLM picks
   the closest specialist (servicing). Cheap path first, smart path second.
