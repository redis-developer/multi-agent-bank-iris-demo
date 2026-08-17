"""Agent memory via Redis Agent Memory (managed, on Redis Cloud).

═══════════════════════════════════════════════════════════════════════
SECTION 5 - AGENT MEMORY: solved.
═══════════════════════════════════════════════════════════════════════

Agent Memory is a managed Redis Iris service: you provision it in the
Redis Cloud console (the Section 5 steps walk through it) and it gives
every agent two tiers of memory over a small REST API:

  * Session memory (short-term) — the ordered event log of one
    conversation session. POST each turn's messages as events; GET the
    session to give the agents the conversation so far.
    POST /v1/stores/{storeId}/session-memory/events

  * Long-term memory — as session events arrive, the service
    **automatically extracts durable facts** ("renovating their home
    this year") in the background — its own LLM, its own embeddings,
    its own vector index — and makes them searchable per customer.
    POST /v1/stores/{storeId}/long-term-memory/search

Notice what is NOT in this file: no extraction prompt, no vectorizer,
no index schema. The managed service owns all of that. Until the three
AGENT_MEMORY_* keys are set in .env, every method is a harmless no-op
and the bot simply stays amnesiac.
"""

import logging
from datetime import datetime, timezone

import httpx

from src import config

logger = logging.getLogger("workshop")

BOT_ACTOR_ID = "bank-bot"


def _utc_now() -> str:
    """Client-supplied event timestamp (the API requires one, in UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class AgentMemory:
    """Thin client over the managed Agent Memory service's REST API."""

    def __init__(self):
        self.configured = all([config.AGENT_MEMORY_URL,
                               config.AGENT_MEMORY_STORE_ID,
                               config.AGENT_MEMORY_API_KEY])
        if not self.configured:
            logger.warning(
                "Agent Memory is not configured — the bot stays amnesiac "
                "until AGENT_MEMORY_URL / AGENT_MEMORY_STORE_ID / "
                "AGENT_MEMORY_API_KEY are set in .env (Section 5).")
            return
        self.http = httpx.Client(
            base_url=(f"{config.AGENT_MEMORY_URL.rstrip('/')}"
                      f"/v1/stores/{config.AGENT_MEMORY_STORE_ID}"),
            headers={"Authorization":
                     f"Bearer {config.AGENT_MEMORY_API_KEY}"},
            timeout=15,
        )

    def session_history(self, session_id: str,
                        limit: int = 12) -> list[dict]:
        """Short-term: the session's prior messages, oldest first, as
        [{"role": "user"|"assistant", "content": str}, ...].

        Provided — it reads back whatever remember_turn wrote: GET the
        session, keep the last `limit` USER/ASSISTANT events, flatten
        each event's content parts into one string.
        """
        if not self.configured:
            return []
        response = self.http.get(f"/session-memory/{session_id}")
        if response.status_code == 404:
            return []  # first turn of a new session
        response.raise_for_status()
        events = response.json().get("events", [])[-limit:]
        return [{"role": e["role"].lower(),
                 "content": " ".join(p.get("text", "") for p in e["content"])}
                for e in events if e["role"] in ("USER", "ASSISTANT")]

    def remember_turn(self, session_id: str, customer_id: str,
                      user_message: str, reply: str) -> None:
        """Create session memory: append this turn to the session as two
        events. The service extracts long-term facts from them on the
        extraction cadence you configured at creation (1 minute). The
        session's owner (the privacy boundary `recall` filters on) is
        taken from the first event's actorId, which is why the
        customer's message must carry their customer_id.

        ═══════════════════════════════════════════════════════════════
        SECTION 5 - AGENT MEMORY (create session memory): each event
        needs who is speaking ("actorId"), their "role", and the message
        "content". Uncomment the parameters below. Solved.
        ═══════════════════════════════════════════════════════════════
        """
        user_event = {
            "actorId": customer_id,
            "role": "USER",
            "content": [{"text": user_message}],
        }
        bot_event = {
            "actorId": BOT_ACTOR_ID,
            "role": "ASSISTANT",
            "content": [{"text": reply}],
        }
        if not self.configured or not user_event or not bot_event:
            return None
        for event in (user_event, bot_event):
            self.http.post("/session-memory/events", json={
                "sessionId": session_id,
                "createdAt": _utc_now(),
                **event,
            }).raise_for_status()

    def clear_all(self) -> dict:
        """Wipe the memory service: delete every session's event log and
        every long-term memory, across all sessions and customers. The
        FAQs, bank records, and other seeded data live in your Redis
        database — not in the memory service — so they are untouched.
        Provided — the chat UI's reset button calls this; not an
        exercise."""
        if not self.configured:
            return {"configured": False,
                    "sessions_deleted": 0, "memories_deleted": 0}
        sessions_deleted = 0
        token = None
        while True:
            params = {"limit": 1000, "includeAll": "true"}
            if token:
                params["pageToken"] = token
            response = self.http.get("/session-memory", params=params)
            response.raise_for_status()
            data = response.json()
            for session_id in data.get("items", []):
                self.http.delete(
                    f"/session-memory/{session_id}").raise_for_status()
                sessions_deleted += 1
            token = data.get("nextPageToken")
            if not token:
                break
        memories_deleted = 0
        for _ in range(1000):  # bulk-delete caps at 100 ids per call
            response = self.http.post("/long-term-memory/search",
                                      json={"limit": 100})
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                break
            self.http.request("DELETE", "/long-term-memory", json={
                "memoryIds": [m["id"] for m in items],
            }).raise_for_status()
            memories_deleted += len(items)
        return {"configured": True,
                "sessions_deleted": sessions_deleted,
                "memories_deleted": memories_deleted}

    def recall(self, customer_id: str, query: str, k: int = 3) -> list[str]:
        """Long-term: up to k extracted facts about this customer,
        closest in meaning to the current message.

        Provided — the entire long-term implementation is one semantic
        search, filtered to this customer's ownerId (the privacy
        boundary). The extraction that *fills* long-term memory is not
        code at all: it runs server-side, on the cadence you set when
        creating the service.
        """
        if not self.configured:
            return []
        response = self.http.post("/long-term-memory/search", json={
            "text": query,
            "filter": {"ownerId": {"eq": customer_id}},
            "limit": k,
        })
        response.raise_for_status()
        return [m["text"] for m in response.json().get("items", [])]
