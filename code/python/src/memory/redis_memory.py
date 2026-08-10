"""Agent memory via the Redis Agent Memory Server (Redis Iris).

═══════════════════════════════════════════════════════════════════════
SECTION 5 - AGENT MEMORY: this file is an exercise file.
═══════════════════════════════════════════════════════════════════════

The Agent Memory Server — the Agent Memory component of Redis Iris — runs
as its own service (the `agent-memory` container) and gives every agent
two tiers of memory over a simple REST API:

  * Working memory (short-term) — the ordered message log of one
    conversation session. GET it before a turn to give the agents the
    conversation so far; PUT the new turn after replying.
    `PUT /v1/working-memory/{session_id}`

  * Long-term memory — as turns are written to working memory, the server
    **automatically extracts durable facts** ("renovating their home this
    year") in the background — its own LLM, its own embeddings, its own
    vector index — and makes them searchable per user.
    `POST /v1/long-term-memory/search`

Notice what is NOT in this file: no extraction prompt, no vectorizer, no
index schema. The memory server owns all of that.
"""

import httpx

from src import config


class AgentMemory:
    """Thin client over the Agent Memory Server's REST API."""

    def __init__(self, base_url: str = config.AGENT_MEMORY_URL):
        self.http = httpx.Client(base_url=base_url, timeout=15)

    def session_history(self, session_id: str,
                        limit: int = 12) -> list[dict]:
        """Short-term: the session's prior messages, oldest first, as
        [{"role": "user"|"assistant", "content": str}, ...].

        ═══════════════════════════════════════════════════════════════
        SECTION 5 - AGENT MEMORY (working memory): GET the session's
        working memory and return its messages (empty list if the session
        does not exist yet).
        ═══════════════════════════════════════════════════════════════
        """
        return []

    def remember_turn(self, session_id: str, customer_id: str,
                      user_message: str, reply: str) -> None:
        """Append this turn to the session's working memory. The server
        extracts long-term facts from it automatically in the background.

        ═══════════════════════════════════════════════════════════════
        SECTION 5 - AGENT MEMORY (working memory): fetch the current
        history, append the user message and the assistant reply, and PUT
        the working memory back with this customer's user_id.
        ═══════════════════════════════════════════════════════════════
        """
        return None

    def recall(self, customer_id: str, query: str, k: int = 3) -> list[str]:
        """Long-term: up to k extracted facts about this customer, closest
        in meaning to the current message.

        ═══════════════════════════════════════════════════════════════
        SECTION 5 - AGENT MEMORY (long-term): POST a semantic search to
        the memory server, filtered to this customer's user_id, and
        return the memory texts.
        ═══════════════════════════════════════════════════════════════
        """
        return []
