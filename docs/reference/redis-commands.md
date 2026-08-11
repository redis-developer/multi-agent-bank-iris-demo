# Redis commands cheat sheet

Run these in the **Redis Insight** panel's Workbench, or from the
**Terminal** panel with `redis-cli -h redis`.

## The bank's data

```bash
# Customers (hashes)
HGETALL customer:CUST1001
SMEMBERS customer:CUST1001:loans

# Loans (JSON)
JSON.GET loan:LAN20240001 $
JSON.GET loan:LAN20220042 $.status

# Pre-approved offers (JSON)
JSON.GET offers:CUST1001 $

# NOCs issued during the workshop
KEYS noc:*
```

## Vector indexes

```bash
# Every index the workshop creates
FT._LIST

# The loan documents index (Section 1/3)
FT.INFO idx:loan_docs

# Full-text over the chunks (classic search still works)
FT.SEARCH idx:loan_docs "@content:foreclosure" RETURN 2 doc_title section

# Filter by product tag
FT.SEARCH idx:loan_docs "@product:{topup_loan}" RETURN 2 doc_title section
```

## Section artifacts

```bash
# Section 2 — the semantic router's reference embeddings
FT.SEARCH wa-journey-router "*" LIMIT 0 5 RETURN 2 reference route_name

# Section 5 — the Agent Memory Server keeps its own keys in this Redis
SCAN 0 MATCH *memory* COUNT 200

# Section 5 — but its REST API is the intended window (from your terminal):
#   curl http://agent-memory:8000/v1/working-memory/
#   curl -s -X POST http://agent-memory:8000/v1/long-term-memory/search \
#     -H 'Content-Type: application/json' \
#     -d '{"text": "renovation", "user_id": {"eq": "CUST1001"}, "limit": 5}'

# Section 6 — semantic cache entries
FT.SEARCH wa-reply-cache "*" LIMIT 0 5 RETURN 2 prompt response

# Loan Account Number counter used by generate_lan
GET counter:lan
```

## Reset tricks

```bash
# Wipe everything and reseed on next api restart
FLUSHALL
# then, from the host: docker compose restart api agent-memory
```
