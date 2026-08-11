"""Semantic routing of WhatsApp messages into journeys.

═══════════════════════════════════════════════════════════════════════
SECTION 2 - SEMANTIC ROUTING: this file is an exercise file.
═══════════════════════════════════════════════════════════════════════

Every incoming WhatsApp message must land in one of five journeys:

  servicing  — existing-customer servicing (status, balance, EMI dates)
  loan_docs  — loan policy questions answered from the loan documents
  noc        — No Objection Certificate for closed loans
  sales      — top-up / balance transfer / home decor / cross-sell
  journey    — the end-to-end loan application journey

A RedisVL SemanticRouter classifies by meaning: each route carries a few
reference utterances, embedded once into Redis; an incoming message matches
the route whose references sit closest in vector space — one embedding
lookup, no LLM call, sub-millisecond routing.
"""

from redisvl.extensions.router import Route, RoutingConfig, SemanticRouter

from src import config
from src.llm.client import get_vectorizer

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 - SEMANTIC ROUTING: define the five routes.
# Each Route needs a name, reference utterances, and a distance threshold.
# Example:
#
#   Route(
#       name="servicing",
#       references=[
#           "what is my loan status",
#           "when is my next EMI due",
#       ],
#       distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
#   ),
# ═══════════════════════════════════════════════════════════════════════
ROUTES: list[Route] = []


def build_router(redis_url: str = config.REDIS_URL) -> SemanticRouter | None:
    """Build the SemanticRouter over ROUTES.

    ═══════════════════════════════════════════════════════════════════
    SECTION 2 - SEMANTIC ROUTING: build and return the SemanticRouter.
    ═══════════════════════════════════════════════════════════════════
    """
    return None


def route_message(router: SemanticRouter | None, message: str) -> str | None:
    """Classify one message; return the route name, or None if no route
    is close enough (the caller falls back to the supervisor's judgment)."""
    if router is None:
        return None
    match = router(message)
    if match is None or not match.name:
        return None
    return match.name
