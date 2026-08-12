## Steps

1. **Point Redis Insight at your cloud database.** Open the **Redis
   Insight** panel from the workbench tabs, choose **Add database
   manually**, and paste the same connection details you put in `.env`
   (host, port, username `default`, password). One time only — the panel
   remembers it.

2. **See the FAQ knowledge base.** In Insight's Workbench, run:

   ```bash
   FT.INFO idx:faqs
   ```

   Note `num_docs` (~20 FAQs) and the `embedding` field: HNSW, cosine,
   1536 dims. Look at one record:

   ```bash
   HGETALL faq:foreclosure-charge
   ```

   Question, answer, `product` tag, and the embedding bytes — one
   retrievable unit per FAQ.

3. **Filter by product.**

   ```bash
   FT.SEARCH idx:faqs "@product:{noc}" RETURN 1 section
   ```

   The `product` tag field answers exact filters instantly — no vectors
   involved.

4. **See semantic beat lexical.** Full-text search needs the right words:

   ```bash
   FT.SEARCH idx:faqs "closing loan early charges" RETURN 1 section
   ```

   Lexical search struggles unless terms match. The bot's retrieval
   (Section 3) will embed the *question* and match by meaning instead.

5. **Look for the bank.**

   ```bash
   SCAN 0 MATCH customer:* COUNT 100
   SCAN 0 MATCH loan:* COUNT 100
   ```

   Empty. The bank's structured records don't exist yet — they arrive in
   Section 4, imported through the Context Retriever into this same
   database. Remember this moment.

6. **Send the bot a message.** In the **App** panel ask
   *"What is the foreclosure charge?"* — the bot already knows this belongs
   to the *loan docs* journey (watch the route chip; that's Section 2's
   router at work) but can only answer with a placeholder. It knows *where*
   every message belongs and nothing about *what to do there*. Closing that
   gap is the rest of the workshop.
