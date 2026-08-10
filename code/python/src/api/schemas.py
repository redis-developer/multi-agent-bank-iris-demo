"""Request/response models for the chat API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    customer_id: str = Field(default="CUST1001")
    session_id: str = Field(default="default-session")


class Citation(BaseModel):
    doc_title: str
    section: str


class ChatResponse(BaseModel):
    reply: str
    route: str
    agent: str
    cached: bool = False
    citations: list[Citation] = []
    latency_ms: int


class CustomerSummary(BaseModel):
    customer_id: str
    name: str
    segment: str
    preapproved: bool


class HealthResponse(BaseModel):
    status: str
    redis: bool
    dataset_loaded: bool
