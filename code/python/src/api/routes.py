"""HTTP endpoints for the WhatsApp-style chat UI."""

from fastapi import APIRouter, Request

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
    r = get_redis()
    result = []
    for key in sorted(r.scan_iter(f"{config.CUSTOMER_KEY_PREFIX}CUST*")):
        if key.count(":") > 1:
            continue  # skip customer:<id>:loans sets
        data = r.hgetall(key)
        if data:
            result.append(CustomerSummary(
                customer_id=data["customer_id"],
                name=data["name"],
                segment=data["segment"],
                preapproved=data.get("preapproved", "False") == "True",
            ))
    return result


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    service = http_request.app.state.chat_service
    return service.chat(request)
