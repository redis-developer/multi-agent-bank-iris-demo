"""The bank's data model for the Redis Context Retriever.

═══════════════════════════════════════════════════════════════════════
SECTION 4 - CONTEXT RETRIEVER: this file is an exercise file.    SOLVED.
═══════════════════════════════════════════════════════════════════════

This is the *semantic model* — the one place the bank's business objects
are described. Each `ContextModel` class declares an entity: where its
records live (`__redis_key_template__`), what its fields mean
(descriptions guide the agents), and which fields are searchable
(`index="tag"` for exact filters, `index="text"` for full-text).

The Context Retriever service turns this model into the agents' retrieval
tools: deploy it (the section's steps) and the service generates get /
filter / search tools for every entity — no tool code written by anyone.
"""

from context_surfaces.context_model import ContextField, ContextModel


# ── provided example ────────────────────────────────────────────────────
class Customer(ContextModel):
    """A bank customer's profile."""

    __redis_key_template__ = "customer:{customer_id}"

    customer_id: str = ContextField(
        description="The customer's ID, e.g. CUST1001",
        is_key_component=True)
    name: str = ContextField(
        description="The customer's full name", index="text")
    segment: str = ContextField(
        description="Relationship segment", index="tag",
        allowed_values=["existing", "new"])
    kyc_status: str = ContextField(
        description="KYC verification status", index="tag",
        allowed_values=["verified", "pending"])
    credit_score: int = ContextField(
        description="Latest bureau credit score")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4 - CONTEXT RETRIEVER (model): make the indexing decisions.
# Solved: every `# TODO` is resolved — the key components form the Redis
# keys, the tag indexes power the agents' filters (loans by owner and
# status, offers by customer), and the text index makes the offer notes
# searchable by meaning of words, not exact values.
# ═══════════════════════════════════════════════════════════════════════
class Loan(ContextModel):
    """A loan account, identified by its LAN."""

    __redis_key_template__ = "loan:{lan}"

    lan: str = ContextField(
        description="The Loan Account Number (LAN), e.g. LAN20240001",
        is_key_component=True)
    customer_id: str = ContextField(
        description="The owning customer's ID", index="tag")
    product: str = ContextField(
        description="The loan product", index="tag",
        allowed_values=["personal_loan", "topup_loan", "home_decor_loan"])
    principal: float = ContextField(
        description="Sanctioned amount in rupees")
    annual_rate: float = ContextField(
        description="Interest rate, percent per annum, reducing balance")
    tenure_months: int = ContextField(
        description="Loan tenure in months")
    emi: float = ContextField(
        description="Monthly instalment (EMI) in rupees")
    outstanding: float = ContextField(
        description="Current outstanding principal in rupees")
    status: str = ContextField(
        description="Loan lifecycle state", index="tag",
        allowed_values=["sanctioned", "active", "closed"])
    disbursed_on: str = ContextField(
        description="Disbursement date (YYYY-MM-DD)", default="")
    closed_on: str = ContextField(
        description="Closure date (YYYY-MM-DD); empty while active",
        default="")


class Offer(ContextModel):
    """A live pre-approved offer for a customer."""

    __redis_key_template__ = "offer:{customer_id}:{product}"

    customer_id: str = ContextField(
        description="The customer the offer belongs to",
        is_key_component=True, index="tag")
    product: str = ContextField(
        description="The offered product", is_key_component=True,
        index="tag")
    amount: float = ContextField(
        description="Pre-approved amount in rupees")
    annual_rate: float = ContextField(
        description="Offered rate, percent per annum")
    max_tenure_months: int = ContextField(
        description="Maximum tenure in months", default=0)
    valid_till: str = ContextField(
        description="Offer expiry date (YYYY-MM-DD)", default="")
    note: str = ContextField(
        description="Offer conditions and pitch notes", index="text",
        default="")


# Every entity in this list is deployed to the Context Retriever surface.
BANK_ENTITIES: list[type[ContextModel]] = [Customer, Loan, Offer]
