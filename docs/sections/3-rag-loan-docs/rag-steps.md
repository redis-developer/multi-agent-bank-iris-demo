## Steps

1. **Read the provided pipeline.** In `code/python/src/chat/service.py`,
   the `loan_docs` branch under the `SECTION 3 - RAG / SECTION 4` banner
   already routes loan questions into `_answer_from_loan_docs` — the whole
   RAG pattern in five lines: `search` (retrieve), `format_context` into
   the system prompt (augment), `llm.invoke` (generate), plus citations
   for the UI. Nothing to write here — until retrieval exists, the helper
   falls back to Section 2's canned reply.

2. **Exercise 1 — vector search.** Open `code/python/src/retrieval/rag.py`,
   find the `SECTION 3 (vector)` banner in `search`, and replace
   `return None` with:

   ```python
   embedding = self.vectorizer.embed(query)
   vector_query = VectorQuery(
       vector=embedding,
       vector_field_name="embedding",
       return_fields=RETURN_FIELDS,
       num_results=k,
   )
   if product:
       vector_query.set_filter(Tag("product") == product)
   results = self.index.query(vector_query)
   return [self._chunk(r, distance=float(r["vector_distance"]))
           for r in results]
   ```

   Embed the question, return the chunks closest in meaning — this is the
   *retrieve* step of RAG, and it turns the whole loan_docs journey on.

3. **Save and test.** The api reloads automatically when files change (uvicorn `--reload`; a second or two), then ask:

   > What is the foreclosure charge on a personal loan?

   The answer now says 4% after 6 EMIs (nil for floating-rate) with `[n]`
   citations, and the pipeline inspector lists which FAQs were retrieved —
   *FAQ — Personal loans — What is the foreclosure charge…* should be
   there.

4. **Try meaning, not keywords.**

   > how much do I pay to close my loan early?

   No shared vocabulary with the document, same grounded answer — the
   vector search matched intent.

5. **Test the honesty path.**

   > what are your gold loan interest rates?

   There is no gold-loan FAQ, so the retrieved entries won't contain the
   answer, and the persona instructs the model to say so rather than invent
   a rate. Grounding is as much about refusing as answering.

6. **(Optional) Watch the retrieval itself.** In the Redis Insight panel, profile a
   query the way the app runs it:

   ```bash
   FT.SEARCH idx:faqs "@product:{personal_loan}" RETURN 1 section
   ```

   and compare with what the inspector showed as citations.

---

### The other two modes: keyword and hybrid

The bot's RAG works on vector search. The next two exercises build the
*other two* retrieval modes and race all three in the **Retrieval lab** —
the tab next to the Pipeline inspector in the **App** view. It calls the
compare endpoint that ships with the app (`GET /api/retrieval/compare` —
provided, in `src/api/routes.py`) and shows each mode's latency and top
hits side by side. Try it now: modes you haven't built yet report *not
implemented*.

7. **Exercise 2 — keyword search.** In `src/retrieval/rag.py`, find the
   `SECTION 3 (keyword)` banner in `keyword_search` and
   replace `return None` with a BM25 full-text query:

   ```python
   text_query = TextQuery(
       text=query,
       text_field_name="content",
       text_scorer="BM25STD",
       return_fields=RETURN_FIELDS,
       num_results=k,
       stopwords=None,
   )
   results = self.index.query(text_query)
   return [self._chunk(r, score=round(float(r["score"]), 2))
           for r in results]
   ```

   No vectorizer, no embedding call — just the inverted index and BM25.

8. **Exercise 3 — hybrid search.** Same file, `SECTION 3 (hybrid)` banner
   in `hybrid_search`:

   ```python
   embedding = self.vectorizer.embed(query)
   hybrid_query = HybridQuery(
       text=query,
       text_field_name="content",
       vector=embedding,
       vector_field_name="embedding",
       vector_search_method="KNN",
       combination_method="RRF",
       return_fields=RETURN_FIELDS,
       num_results=k,
       stopwords=None,
   )
   results = self.index.query(hybrid_query)
   return [self._chunk(r) for r in results]
   ```

   One query object, and Redis runs the text path and the KNN path and
   fuses the ranked lists with RRF — that's `FT.HYBRID` under the hood.

9. **Race them: exact jargon.** Save, then in the Retrieval lab click
   the first preset:

   > NOC

   Keyword pins both NOC FAQs in a single Redis round trip. Vector
   reaches the same hits but pays for an embedding call first — compare
   the latency chips. When the query *is* the term, the inverted index
   is unbeatable.

10. **Race them: pure paraphrase.** Click the second preset:

    > how much do I pay to end my loan before the tenure finishes

    Now keyword whiffs — it matches stray words ("loan", "pay") and
    returns the NOC FAQ, nowhere near the question. Vector lands on the
    *ending-the-loan-early* FAQs (part-prepayment, foreclosure) because it
    matched the meaning. This asymmetry is why RAG defaults to vector
    search.

11. **Race them: mixed query.** Click the third preset:

    > processing fee to close my loan before the tenure ends

    The query has an exact anchor (*processing fee*) **and** a paraphrase
    (*close before the tenure ends* → foreclosure). Keyword anchors on the
    fee words and never finds foreclosure — the actual answer. Vector puts
    foreclosure first. Hybrid's fused list keeps both signals: the fee FAQ
    on top *and* foreclosure in the top 3 — RRF merges the two rankings
    instead of asking you to pick a mode.

    (Prefer the raw JSON? The same races run from the **Terminal** panel:
    `curl -s "http://api:8000/api/retrieval/compare?q=...&k=3" | jq`.)

12. **(Optional) Full-text tricks in Redis Insight.** The `TEXT` index does
    more than exact terms — try these in the Redis Insight panel:

    ```bash
    FT.SEARCH idx:faqs "%forclosure%" RETURN 1 section
    FT.SEARCH idx:faqs "\"balance transfer\"" RETURN 1 section
    FT.SEARCH idx:faqs "disburs*" RETURN 1 section
    ```

    Fuzzy matching (`%…%` tolerates the typo), exact phrases, and prefix
    matching — all from the same index your keyword search uses.

13. **(Optional) Make the bot retrieve hybrid.** One line in
    `_answer_from_loan_docs` (in `service.py`) upgrades the RAG itself:

    ```python
    chunks = self.retriever.hybrid_search(message) or self.retriever.search(message)
    ```

    The workshop solutions keep vector as the default for clarity, but in
    production a servicing bot fields jargon and paraphrase in the same
    minute — hybrid is usually the right answer.
