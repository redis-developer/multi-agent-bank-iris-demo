"""The chat pipeline — every WhatsApp message flows through here.

═══════════════════════════════════════════════════════════════════════
SOLVED THROUGH SECTION 5.
═══════════════════════════════════════════════════════════════════════

  message ──► semantic cache ──► semantic router ──► recall memories
                 (Section 6)        (Section 2)        (Section 5)
                                        │
                                        ▼
                              multi-agent graph (Section 4)
                              └─ RAG loan_docs agent (Section 3)
                                        │
                                        ▼
                    remember facts ──► store in cache ──► reply
                      (Section 5)        (Section 6)
"""

import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src import config
from src.agents.graph import build_agent_graph
from src.api.schemas import ChatRequest, ChatResponse, Citation
from src.cache.semantic_cache import ReplyCache
from src.llm.client import get_llm
from src.memory.redis_memory import AgentMemory
from src.retrieval.rag import LoanDocsRetriever
from src.router.semantic_router import build_router, route_message

CANNED_REPLIES = {
    "servicing": "You've reached the *servicing* journey — loan status, "
                 "balances, and EMI dates. (The servicing agent goes live in "
                 "Section 4.)",
    "loan_docs": "You've reached the *loan docs* journey — questions about "
                 "rates, charges, and policies. (Grounded answers arrive in "
                 "Section 3.)",
    "noc": "You've reached the *NOC* journey — closure certificates for "
           "closed loans. (The NOC agent goes live in Section 4.)",
    "sales": "You've reached the *sales* journey — top-ups, balance "
             "transfers, and home decor loans. (The sales agent goes live in "
             "Section 4.)",
    "journey": "You've reached the *loan journey* — EMI quotes, documents, "
               "LAN, and disbursement. (The journey agent goes live in "
               "Section 4.)",
}

FALLBACK_REPLY = ("Namaste! I'm your bank's WhatsApp assistant. I can help "
                  "with your existing loans, loan policy questions, NOCs for "
                  "closed loans, offers, and new loan applications — but my "
                  "brain is still being built, section by section.")


class ChatService:
    def __init__(self):
        self.llm = get_llm()
        self.retriever = LoanDocsRetriever()
        self.router = build_router()                      # Section 2
        self.memory = AgentMemory()                       # Section 5
        self.graph = build_agent_graph(self.llm,
                                       self.retriever)    # Section 4
        self.cache = ReplyCache()                         # Section 6

    def chat(self, request: ChatRequest) -> ChatResponse:
        t0 = time.perf_counter()

        # ── SECTION 6 - SEMANTIC CACHING: check the cache before any work ──
        cached_reply = None

        if cached_reply is not None:
            return self._response(cached_reply, route="cache", agent="cache",
                                  cached=True, t0=t0)

        # ── SECTION 2 - SEMANTIC ROUTING: classify the message ─────────────
        route = route_message(self.router, request.message)

        # ── SECTION 5 - AGENT MEMORY: recall this customer's context ───────
        history = self.memory.session_history(request.session_id)
        memories = self.memory.recall(request.customer_id, request.message)

        # ── SECTION 3 - RAG / SECTION 4 - MULTI-AGENT: generate the reply ──
        reply, agent, citations = self._run_graph(request, route, memories,
                                                  history)

        # ── SECTION 5 - AGENT MEMORY: remember this turn ───────────────────
        self.memory.remember_turn(request.session_id, request.customer_id,
                                  request.message, reply)

        # ── SECTION 6 - SEMANTIC CACHING: store shareable replies ──────────

        return self._response(reply, route=route, agent=agent,
                              citations=citations, t0=t0)

    # ── helpers (provided — used as the sections come online) ──────────────

    def _canned_reply(self, route: str | None) -> str:
        """Section 2: prove routing works before any agent exists."""
        return CANNED_REPLIES.get(route, FALLBACK_REPLY)

    def _answer_from_loan_docs(self, message: str):
        """Section 3: RAG — retrieve policy chunks, augment, generate."""
        from src.agents import personas
        chunks = self.retriever.search(message)
        system = (personas.LOAN_DOCS["prompt"]
                  + "\n\nContext passages:\n"
                  + self.retriever.format_context(chunks))
        response = self.llm.invoke([SystemMessage(content=system),
                                    HumanMessage(content=message)])
        citations = [{"doc_title": c["doc_title"], "section": c["section"]}
                     for c in chunks]
        return response.content, "loan_docs", citations

    def _run_graph(self, request: ChatRequest, route: str | None,
                   memories: list[str], history: list[dict]):
        """Section 4: hand the turn to the multi-agent graph. `history`
        (Section 5) is the session's prior turns from working memory."""
        if self.graph is None:
            return self._canned_reply(route), route or "fallback", []
        prior = [HumanMessage(content=m["content"]) if m["role"] == "user"
                 else AIMessage(content=m["content"]) for m in history]
        result = self.graph.invoke({
            "messages": prior + [HumanMessage(content=request.message)],
            "customer_id": request.customer_id,
            "route": route,
            "memories": memories,
            "citations": [],
        })
        return (result["messages"][-1].content,
                result.get("agent", "supervisor"),
                result.get("citations", []))

    @staticmethod
    def _response(reply: str, *, route: str | None, agent: str, t0: float,
                  cached: bool = False,
                  citations: list[dict] | None = None) -> ChatResponse:
        return ChatResponse(
            reply=reply,
            route=route or "none",
            agent=agent,
            cached=cached,
            citations=[Citation(**c) for c in (citations or [])],
            latency_ms=round((time.perf_counter() - t0) * 1000),
        )
