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
# SECTION 4 - CONTEXT RETRIEVER (model): make the indexing decisions.
#
# The Loan and Offer entities are already written — every field, typed
# and described. What's missing is how each field is *accessed*: which
# fields form the Redis key, which are filterable, which are searchable.
#
# Seven decisions, each marked  # TODO(<field>)  — the name says which
# field it belongs to, and that field is always DIRECTLY BELOW the
# comment. Copy the argument(s) from the comment into that field's
# ContextField(...) call. Like this:
#
#   Before:
#       lan: str = ContextField(
#           description="The Loan Account Number (LAN), e.g. LAN20240001")
#   After:
#       lan: str = ContextField(
#           description="The Loan Account Number (LAN), e.g. LAN20240001",
#           is_key_component=True)
#
# The other fields (principal, emi, dates, ...) need nothing — leave
# them as they are. The deploy (step 6) checks every decision and lists
# any that are still missing.
# ═══════════════════════════════════════════════════════════════════════
class Loan(ContextModel):
    """A loan account, identified by its LAN."""

    __redis_key_template__ = "loan:{lan}"

    # TODO(lan) — the key "loan:{lan}" is built from this field.
    #   Add to the ContextField below:
    #       is_key_component=True
    lan: str = ContextField(
        description="The Loan Account Number (LAN), e.g. LAN20240001")

    # TODO(customer_id) — "what's the outstanding on MY loans?" means
    #   filtering loans by owner. Add to the ContextField below:
    #       index="tag"
    customer_id: str = ContextField(
        description="The owning customer's ID")

    # TODO(product) — agents filter by product, and the values are a
    #   closed set. Add to the ContextField below:
    #       index="tag",
    #       allowed_values=["personal_loan", "topup_loan",
    #                       "home_decor_loan"]
    product: str = ContextField(
        description="The loan product")

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

    # TODO(status) — the NOC agent needs closed loans only.
    #   Add to the ContextField below:
    #       index="tag",
    #       allowed_values=["sanctioned", "active", "closed"]
    status: str = ContextField(
        description="Loan lifecycle state")

    disbursed_on: str = ContextField(
        description="Disbursement date (YYYY-MM-DD)", default="")
    closed_on: str = ContextField(
        description="Closure date (YYYY-MM-DD); empty while active",
        default="")


class Offer(ContextModel):
    """A live pre-approved offer for a customer."""

    __redis_key_template__ = "offer:{customer_id}:{product}"

    # TODO(customer_id) — half of the composite key
    #   "offer:{customer_id}:{product}", and the sales agent filters
    #   offers by customer. Add to the ContextField below:
    #       is_key_component=True, index="tag"
    customer_id: str = ContextField(
        description="The customer the offer belongs to")

    # TODO(product) — the other half of the key, also filterable.
    #   Add to the ContextField below:
    #       is_key_component=True, index="tag"
    product: str = ContextField(
        description="The offered product")

    amount: float = ContextField(
        description="Pre-approved amount in rupees")
    annual_rate: float = ContextField(
        description="Offered rate, percent per annum")
    max_tenure_months: int = ContextField(
        description="Maximum tenure in months", default=0)
    valid_till: str = ContextField(
        description="Offer expiry date (YYYY-MM-DD)", default="")

    # TODO(note) — pitch notes are prose, matched by words rather than
    #   exact values. Add to the ContextField below:
    #       index="text"
    note: str = ContextField(
        description="Offer conditions and pitch notes", default="")


# Every entity in this list is deployed to the Context Retriever surface.
BANK_ENTITIES: list[type[ContextModel]] = [Customer, Loan, Offer]
