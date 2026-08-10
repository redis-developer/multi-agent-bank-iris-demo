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

4. **Restart and ask a policy question.** `docker compose restart api`, then:

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

7. **(Optional) Watch the retrieval itself.** In Redis Insight, profile a
   query the way the app runs it:

   ```bash
   FT.SEARCH idx:loan_docs "@product:{personal_loan}" RETURN 2 doc_title section
   ```

   and compare with what the inspector showed as citations.
