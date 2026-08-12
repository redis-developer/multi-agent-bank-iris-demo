# Redis commands cheat sheet

Run these in the **Redis Insight** panel's Workbench, or from the
**Terminal** panel with `redis-cli -h redis`.

## The bank's data (exists after Section 4's Context Retriever import)

```bash
# Customers / loans / offers — key patterns come from the semantic model
SCAN 0 MATCH customer:* COUNT 100
SCAN 0 MATCH loan:* COUNT 100
SCAN 0 MATCH offer:* COUNT 100

# Loans the bot sanctions itself are JSON
JSON.GET loan:LAN20260001 $

# NOCs issued during the workshop
KEYS noc:*
```

## Vector indexes

```bash
# Every index the workshop creates
FT._LIST

# The FAQ index (Sections 1/3)
FT.INFO idx:faqs

# Full-text over the FAQs (classic search still works)
FT.SEARCH idx:faqs "@content:foreclosure" RETURN 1 section

# Filter by product tag
FT.SEARCH idx:faqs "@product:{topup_loan}" RETURN 1 section
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

# Section 6 — the cache lives in LangCache (Redis Cloud), not this Redis.
# Inspect it via its REST API from the Terminal panel:
#   curl -s -X POST "$LANGCACHE_URL/v1/caches/$LANGCACHE_CACHE_ID/entries/search" \
#     -H "Authorization: Bearer $LANGCACHE_API_KEY" \
#     -H 'Content-Type: application/json' -d '{"prompt": "foreclosure charges?"}'

# Loan Account Number counter used by generate_lan
GET counter:lan
```

## Reset tricks

```bash
# Wipe everything and reseed on next api restart
FLUSHALL
# then, from the host: docker compose restart api agent-memory
```
