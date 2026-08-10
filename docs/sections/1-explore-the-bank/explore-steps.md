## Steps

1. **Meet a customer.** In Redis Insight (<http://localhost:5540>) open the
   Workbench and run:

   ```bash
   HGETALL customer:CUST1001
   SMEMBERS customer:CUST1001:loans
   ```

   Ananya Sharma has two personal loans — one active, one closed. Keep her in
   mind: she is the workshop's main persona.

2. **Read her loans.**

   ```bash
   JSON.GET loan:LAN20240001 $
   JSON.GET loan:LAN20220042 $.status
   ```

   The closed loan (`LAN20220042`) is what the NOC journey will act on in
   Section 4.

3. **Check her offers.**

   ```bash
   JSON.GET offers:CUST1001 $
   ```

   A pre-approved top-up and a festive personal loan — the raw material for
   the sales agent's cross-sell pitch.

4. **Inspect the vector index.**

   ```bash
   FT.INFO idx:loan_docs
   FT.SEARCH idx:loan_docs "@product:{noc}" RETURN 2 doc_title section
   ```

   Note `num_docs` (the chunk count) and the `embedding` vector field: HNSW,
   cosine, 1536 dims.

5. **See semantic beat lexical.** Full-text search needs the right words:

   ```bash
   FT.SEARCH idx:loan_docs "closing loan early charges" RETURN 2 doc_title section
   ```

   Lexical search struggles unless terms match. The bot's retrieval
   (Section 3) will embed the *question* and match by meaning instead.

6. **Send the bot a message.** In the chat UI (<http://localhost:3000>) ask
   *"What is the foreclosure charge?"* — you get the fallback reply. The data
   is all here; the brain isn't. That's the rest of the workshop.
