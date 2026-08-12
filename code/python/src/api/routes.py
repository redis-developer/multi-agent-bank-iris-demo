"""HTTP endpoints for the WhatsApp-style chat UI."""

from fastapi import APIRouter, HTTPException, Request

from src import config
from src.api.schemas import (ChatRequest, ChatResponse, CustomerSummary,
                             HealthResponse)
from src.data.loader import get_redis

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        r = get_redis()
        redis_ok = bool(r.ping())
        loaded = bool(r.exists("workshop:loaded"))
    except Exception:
        redis_ok, loaded = False, False
    return HealthResponse(status="ok" if redis_ok else "degraded",
                          redis=redis_ok, dataset_loaded=loaded)


@router.get("/customers", response_model=list[CustomerSummary])
def customers() -> list[CustomerSummary]:
    """The demo personas for the chat UI. Served from the seed file: the
    customers' *records* only enter the database in Section 4, imported
    through the Context Retriever."""
    import json
    dataset = json.loads((config.DATA_DIR / "customers.json").read_text())
    return [CustomerSummary(
                customer_id=c["customer_id"], name=c["name"],
                segment=c["segment"], preapproved=bool(c.get("preapproved")))
            for c in dataset["customers"]]


@router.post("/context/deploy")
async def context_deploy() -> dict:
    """Deploy the Section 4 semantic model to the Redis Context Retriever
    service (creates the surface, mints an agent key, imports the bank's
    records). Provided — not an exercise."""
    from src.context.deploy import deploy
    try:
        return await deploy()
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"}


@router.get("/context/tools")
def context_tools() -> dict:
    """The generated tool surface the agents currently hold."""
    from src.context.retriever import context_read_tools, stored_deployment
    tools = context_read_tools()
    return {
        "deployment": stored_deployment() and {
            "surface_id": stored_deployment().get("surface_id")},
        "tools": [{"name": t.name, "description": t.description}
                  for t in tools],
    }


@router.get("/retrieval/compare")
def retrieval_compare(q: str, k: int = 3, http_request: Request = None) -> dict:
    """Race the three retrieval modes over the loan-docs index (Section 3,
    'going deeper'). Provided — not an exercise."""
    import time

    service = http_request.app.state.chat_service
    if service is None:
        return {"error": "chat pipeline not started — check OPENAI_API_KEY"}
    retriever = service.retriever

    modes = {
        "keyword": retriever.keyword_search,
        "vector": retriever.search,
        "hybrid": retriever.hybrid_search,
    }
    report: dict = {"query": q, "modes": {}}
    for mode, fn in modes.items():
        t0 = time.perf_counter()
        try:
            chunks = fn(q, k)
        except Exception as error:
            report["modes"][mode] = {"error": str(error)}
            continue
        latency_ms = round((time.perf_counter() - t0) * 1000)
        if chunks is None:
            report["modes"][mode] = {
                "status": "not implemented yet — see the SECTION 3 GOING "
                          "DEEPER banner in src/retrieval/rag.py"}
            continue
        report["modes"][mode] = {
            "latency_ms": latency_ms,
            "results": [
                {
                    "rank": i,
                    "doc_title": c["doc_title"],
                    "section": c["section"],
                    **({"bm25_score": c["score"]} if "score" in c else {}),
                    **({"distance": round(c["distance"], 3)}
                       if "distance" in c else {}),
                    "snippet": c["content"][:90] + "…",
                }
                for i, c in enumerate(chunks, start=1)
            ],
        }
    return report


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    service = http_request.app.state.chat_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="The chat pipeline failed to start — usually a missing "
                   "or invalid OPENAI_API_KEY in .env. Fix it, then run: "
                   "docker compose restart api",
        )
    return service.chat(request)
