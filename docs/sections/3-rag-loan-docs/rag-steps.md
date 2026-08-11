## Steps

1. **Read the retrieval you already have.** Open
   `code/python/src/retrieval/rag.py` — provided, not an exercise.
   `LoanDocsRetriever.search` embeds the query and runs a RedisVL
   `VectorQuery` over `idx:loan_docs`; `format_context` lays chunks out as
   numbered `[1] Document — Section` entries. Retrieval exists — nothing
   calls it yet.

2. **Read the provided helper.** In `code/python/src/chat/service.py`, find
   `_answer_from_loan_docs`. It is the whole RAG pattern in five lines:
   `search` (retrieve), `format_context` into the system prompt (augment),
   `llm.invoke` (generate), plus citations for the UI.

3. **Route loan questions through it.** Under the
   `SECTION 3 - RAG / SECTION 4 - MULTI-AGENT` banner, replace the canned
   reply from Section 2 with:

   ```python
   if route == "loan_docs":
       reply, agent, citations = self._answer_from_loan_docs(
           request.message)
   else:
       reply, agent, citations = (self._canned_reply(route),
                                  route or "fallback", [])
   ```

4. **Save and test.** The api reloads automatically when files change (uvicorn `--reload`; a second or two), then ask:

   > What is the foreclosure charge on a personal loan?

   The answer now says 4% after 6 EMIs (nil for floating-rate) with `[n]`
   citations, and the pipeline inspector lists which document sections were
   retrieved — *Personal Loan Product Guide — Foreclosure and
   part-prepayment* should be there.

5. **Try meaning, not keywords.**

   > how much do I pay to close my loan early?

   No shared vocabulary with the document, same grounded answer — the
   vector search matched intent.

6. **Test the honesty path.**

   > what are your gold loan interest rates?

   There is no gold loan document, so the retrieved chunks won't contain the
   answer, and the persona instructs the model to say so rather than invent
   a rate. Grounding is as much about refusing as answering.

7. **(Optional) Watch the retrieval itself.** In the Redis Insight panel, profile a
   query the way the app runs it:

   ```bash
   FT.SEARCH idx:loan_docs "@product:{personal_loan}" RETURN 2 doc_title section
   ```

   and compare with what the inspector showed as citations.

---

### Going deeper: keyword, vector, hybrid

The bot's RAG works. These exercises make you build the *other two*
retrieval modes and race all three, using the compare endpoint that ships
with the app (`GET /api/retrieval/compare` — provided, in
`src/api/routes.py`).

8. **Implement keyword search.** In `src/retrieval/rag.py`, find the
   `SECTION 3 - GOING DEEPER (keyword)` banner in `keyword_search` and
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

9. **Implement hybrid search.** Same file, `SECTION 3 - GOING DEEPER
   (hybrid)` banner in `hybrid_search`:

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

10. **Race them: exact jargon.** Save, then in the **Terminal** panel:

    ```bash
    curl -s "http://api:8000/api/retrieval/compare?q=eNACH+mandate+registration&k=2" | jq
    ```

    Keyword answers in ~2 ms and pins the Disbursement section exactly.
    Vector needs an embedding round trip (~300 ms) for the same top hit.
    When the query *is* the term, the inverted index is unbeatable.

11. **Race them: pure paraphrase.**

    ```bash
    curl -s "http://api:8000/api/retrieval/compare?q=how+much+do+I+pay+to+end+my+loan+before+the+tenure+finishes&k=2" | jq
    ```

    Now keyword whiffs — it matches stray words ("loan", "pay") and returns
    the *Top-up Guide*, nowhere near the answer. Vector lands on
    *Foreclosure and part-prepayment* because it matched the meaning. This
    asymmetry is why RAG defaults to vector search.

12. **Race them: mixed query.**

    ```bash
    curl -s "http://api:8000/api/retrieval/compare?q=penalty+for+ending+my+eNACH+loan+early&k=3" | jq
    ```

    The query has an exact anchor (*eNACH*) **and** a paraphrase (*penalty
    for ending early* → foreclosure). Keyword finds the eNACH doc but not
    foreclosure; vector finds foreclosure but ranks the eNACH doc last.
    Hybrid's fused list surfaces **both** in the top 3 — neither mode alone
    covers the query, RRF does.

13. **(Optional) Full-text tricks in Redis Insight.** The `TEXT` index does
    more than exact terms — try these in the Redis Insight panel:

    ```bash
    FT.SEARCH idx:loan_docs "%forclosure%" RETURN 2 doc_title section
    FT.SEARCH idx:loan_docs "\"balance transfer\"" RETURN 1 doc_title
    FT.SEARCH idx:loan_docs "disburs*" RETURN 1 section
    ```

    Fuzzy matching (`%…%` tolerates the typo), exact phrases, and prefix
    matching — all from the same index your keyword search uses.

14. **(Optional) Make the bot retrieve hybrid.** One line in
    `_answer_from_loan_docs` (in `service.py`) upgrades the RAG itself:

    ```python
    chunks = self.retriever.hybrid_search(message) or self.retriever.search(message)
    ```

    The workshop solutions keep vector as the default for clarity, but in
    production a servicing bot fields jargon and paraphrase in the same
    minute — hybrid is usually the right answer.
