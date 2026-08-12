"""The bank's data model for the Redis Context Retriever.

═══════════════════════════════════════════════════════════════════════
SECTION 4 - CONTEXT RETRIEVER: this file is an exercise file.
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
# SECTION 4 - CONTEXT RETRIEVER (model): declare the remaining entities —
# Loan and Offer — following the Customer example above.
#
#   Loan  — key "loan:{lan}"; looked up by lan (is_key_component). Fields:
#           customer_id (tag), product (tag: personal_loan / topup_loan /
#           home_decor_loan), principal, annual_rate, tenure_months, emi,
#           outstanding, status (tag: sanctioned / active / closed),
#           disbursed_on, closed_on. Give every field a description the
#           agents can act on.
#   Offer — key "offer:{customer_id}:{product}"; both key components.
#           Fields: amount, annual_rate, max_tenure_months, valid_till,
#           note (text-indexed).
#
# Then add both classes to BANK_ENTITIES below.
# ═══════════════════════════════════════════════════════════════════════


# Every entity in this list is deployed to the Context Retriever surface.
BANK_ENTITIES: list[type[ContextModel]] = [Customer]
