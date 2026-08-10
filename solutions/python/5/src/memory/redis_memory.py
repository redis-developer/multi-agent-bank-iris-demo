"""Agent memory via the Redis Agent Memory Server (Redis Iris).

═══════════════════════════════════════════════════════════════════════
SECTION 5 - AGENT MEMORY: solved.
═══════════════════════════════════════════════════════════════════════

The Agent Memory Server — the Agent Memory component of Redis Iris — runs
as its own service (the `agent-memory` container) and gives every agent
two tiers of memory over a simple REST API:

  * Working memory (short-term) — the ordered message log of one
    conversation session.
  * Long-term memory — durable facts the server **automatically extracts**
    from working memory in the background, searchable per user.

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
        [{"role": "user"|"assistant", "content": str}, ...]."""
        response = self.http.get(
            f"/v1/working-memory/{session_id}",
            params={"recent_messages_limit": limit},
        )
        if response.status_code == 404:
            return []  # first turn of a new session
        response.raise_for_status()
        return [{"role": m["role"], "content": m["content"]}
                for m in response.json().get("messages", [])]

    def remember_turn(self, session_id: str, customer_id: str,
                      user_message: str, reply: str) -> None:
        """Append this turn to the session's working memory. The server
        extracts long-term facts from it automatically in the background."""
        messages = self.session_history(session_id, limit=50)
        messages += [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        self.http.put(
            f"/v1/working-memory/{session_id}",
            json={"messages": messages, "user_id": customer_id},
        ).raise_for_status()

    def recall(self, customer_id: str, query: str, k: int = 3) -> list[str]:
        """Long-term: up to k extracted facts about this customer, closest
        in meaning to the current message."""
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
