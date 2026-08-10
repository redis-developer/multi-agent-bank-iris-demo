"""Semantic routing of WhatsApp messages into journeys.

═══════════════════════════════════════════════════════════════════════
SECTION 2 - SEMANTIC ROUTING: solved.
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

from redisvl.extensions.router import Route, SemanticRouter

from src import config
from src.llm.client import get_vectorizer

ROUTES: list[Route] = [
    Route(
        name="servicing",
        references=[
            "what is my loan status",
            "what's my outstanding balance",
            "when is my next EMI due",
            "show my repayment history",
            "I need my loan statement",
            "my EMI got debited twice, please check",
        ],
        distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
    ),
    Route(
        name="loan_docs",
        references=[
            "what documents are needed for a personal loan",
            "what is the foreclosure charge",
            "what are the interest rates on personal loans",
            "am I eligible for a personal loan",
            "how is EMI calculated on reducing balance",
            "what is the processing fee",
            "explain the rules for balance transfer",
        ],
        distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
    ),
    Route(
        name="noc",
        references=[
            "I need an NOC for my closed loan",
            "send me my loan closure certificate",
            "issue a no objection certificate",
            "my loan is closed but the bureau still shows it active",
            "where is my NOC, it has been two weeks",
        ],
        distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
    ),
    Route(
        name="sales",
        references=[
            "I want a top up on my existing loan",
            "can I transfer my loan to get a lower rate",
            "I want a loan for renovating my home",
            "do I have any pre-approved offers",
            "tell me about the home decor loan",
            "I need some extra funds, what are my options",
        ],
        distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
    ),
    Route(
        name="journey",
        references=[
            "I want to apply for the loan now",
            "calculate the EMI for 5 lakhs over 4 years",
            "here are my documents, please verify them",
            "generate my loan account number",
            "please disburse my loan",
            "I accept the offer, let's proceed",
        ],
        distance_threshold=config.ROUTER_DISTANCE_THRESHOLD,
    ),
]


def build_router(redis_url: str = config.REDIS_URL) -> SemanticRouter | None:
    """Build the SemanticRouter over ROUTES. The reference utterances are
    embedded and stored in Redis under the router's own index."""
    return SemanticRouter(
        name=config.ROUTER_NAME,
        vectorizer=get_vectorizer(),
        routes=ROUTES,
        redis_url=redis_url,
        overwrite=True,
    )


def route_message(router: SemanticRouter | None, message: str) -> str | None:
    """Classify one message; return the route name, or None if no route
    is close enough (the caller falls back to the supervisor's judgment)."""
    if router is None:
        return None
    match = router(message)
    if match is None or not match.name:
        return None
    return match.name
