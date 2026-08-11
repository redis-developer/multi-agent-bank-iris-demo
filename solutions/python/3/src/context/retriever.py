"""A miniature Redis Context Retriever — schema-first, governed data access.

═══════════════════════════════════════════════════════════════════════
SECTION 4 - CONTEXT RETRIEVER: this file is an exercise file.
═══════════════════════════════════════════════════════════════════════

Hand-coding one tool per query ("get loans", "get offers", "get profile",
…) is how agent projects sprawl into a tool zoo. Redis Iris's Context
Retriever inverts it: declare the *semantic model* of your business data
once — entities, fields, key patterns, ownership — and the retrieval
tools are **generated** from the model, with access rules enforced by the
retriever itself rather than by prompt instructions.

This file is a working miniature of that idea:

  ENTITIES          the semantic model of the bank's operational data
  ContextRetriever  generates the agents' read-tool surface from it
  _governed_fetch   row-level governance: every fetch is scoped to the
                    verified customer — an agent (or a manipulated LLM)
                    asking for someone else's record is refused HERE,
                    not by prompt luck

The managed version (Redis Cloud) does this as a service: `pip install
redis-context-retriever`, model entities with the `ctxctl` CLI or the
Cloud UI, and agents call the generated tools over MCP with scoped agent
keys and access tags.
"""

import json
from dataclasses import dataclass, field

from langchain_core.tools import StructuredTool

from src import config
from src.data.loader import get_redis


@dataclass
class Entity:
    """One business object in the semantic model."""
    name: str                 # entity name; feeds generated tool names
    description: str          # feeds generated tool descriptions
    key_pattern: str          # where records live, e.g. "loan:{id}"
    storage: str              # "hash" or "json"
    id_field: str             # the field agents look records up by
    fields: dict = field(default_factory=dict)   # field -> meaning
    owner_field: str | None = None  # field naming the owning customer;
                                    # None = the record id IS the customer id
    owned_set: str | None = None    # reverse index of a customer's records


ENTITIES: dict[str, Entity] = {
    # ── provided example ────────────────────────────────────────────────
    "customer": Entity(
        name="customer",
        description="A bank customer's profile.",
        key_pattern=f"{config.CUSTOMER_KEY_PREFIX}{{id}}",
        storage="hash",
        id_field="customer_id",
        fields={
            "name": "full name",
            "segment": "existing or new customer",
            "kyc_status": "verified or pending",
            "credit_score": "bureau score",
            "preapproved": "whether pre-approved offers exist",
        },
    ),
    # ═══════════════════════════════════════════════════════════════════
    # SECTION 4 - CONTEXT RETRIEVER (model): declare the remaining
    # entities, following the "customer" example above. The tools are
    # generated the moment the entities exist.
    #
    #   "loan"   — JSON records at  loan:{id}, looked up by lan; owned
    #              via the record's customer_id field (owner_field), with
    #              the reverse index  customer:{owner}:loans (owned_set)
    #   "offers" — JSON records at  offers:{id}, looked up by customer_id
    # ═══════════════════════════════════════════════════════════════════
}


class ContextRetriever:
    """Generates the governed read-tool surface from ENTITIES."""

    def __init__(self, redis_url: str = config.REDIS_URL):
        self.redis = get_redis()

    # ── raw record access (provided) ────────────────────────────────────

    def _get_record(self, entity: Entity, record_id: str):
        key = entity.key_pattern.format(id=record_id)
        if entity.storage == "hash":
            return self.redis.hgetall(key) or None
        return self.redis.json().get(key)

    # ── governance ──────────────────────────────────────────────────────

    def _governed_fetch(self, entity: Entity, record_id: str,
                        verified_customer_id: str):
        """Fetch a record, enforcing row-level access: only records owned
        by the verified customer come back.

        ═══════════════════════════════════════════════════════════════
        SECTION 4 - CONTEXT RETRIEVER (governance): fetch the record,
        work out its owner (owner_field when set, else the record id
        itself), and refuse anything the verified customer does not own.
        ═══════════════════════════════════════════════════════════════
        """
        return ("The context retriever's governance is not implemented "
                "yet (Section 4 exercise) — no records can be released.")

    # ── generated tool surface (provided) ───────────────────────────────

    def build_tools(self) -> dict[str, StructuredTool]:
        """Generate one get-tool per entity (plus a list-tool where the
        model declares a reverse index). Names, descriptions, and argument
        docs all come from the model — no per-tool code."""
        tools: dict[str, StructuredTool] = {}
        for entity in ENTITIES.values():
            get_name = f"get_{entity.name}"
            tools[get_name] = self._make_get_tool(entity, get_name)
            if entity.owned_set:
                list_name = f"list_customer_{entity.name}s"
                tools[list_name] = self._make_list_tool(entity, list_name)
        return tools

    def _make_get_tool(self, entity: Entity, name: str) -> StructuredTool:
        def get_record(record_id: str, customer_id: str) -> str:
            result = self._governed_fetch(entity, record_id, customer_id)
            return result if isinstance(result, str) else json.dumps(result)

        field_docs = "; ".join(f"{f}: {d}" for f, d in entity.fields.items())
        return StructuredTool.from_function(
            func=get_record,
            name=name,
            description=(f"Fetch one {entity.name} by its {entity.id_field}"
                         f" (pass as record_id). {entity.description} "
                         f"Fields — {field_docs}. Access is scoped to the "
                         f"verified customer."),
        )

    def _make_list_tool(self, entity: Entity, name: str) -> StructuredTool:
        def list_records(customer_id: str) -> str:
            ids = sorted(self.redis.smembers(
                entity.owned_set.format(owner=customer_id)))
            if not ids:
                return f"No {entity.name}s found for this customer."
            fetched = [self._governed_fetch(entity, rid, customer_id)
                       for rid in ids]
            granted = [r for r in fetched if not isinstance(r, str)]
            if granted:
                return json.dumps(granted)
            return fetched[0]  # surface the retriever's refusal/message

        return StructuredTool.from_function(
            func=list_records,
            name=name,
            description=(f"List every {entity.name} belonging to the "
                         f"verified customer. {entity.description}"),
        )


def _placeholder_tool(name: str) -> StructuredTool:
    """Stands in for a tool whose entity isn't in the model yet, so the
    agents keep working (and say why) while the exercise is unsolved."""
    def missing(record_id: str = "", customer_id: str = "") -> str:
        return (f"The context retriever has no '{name}' tool yet — its "
                "entity is not declared in the semantic model "
                "(Section 4 exercise, src/context/retriever.py).")
    return StructuredTool.from_function(
        func=missing, name=name,
        description=f"[not generated yet] {name} — the entity behind this "
                    "tool is missing from the context retriever's model.")


class _ToolSurface(dict):
    def __missing__(self, name: str) -> StructuredTool:
        return _placeholder_tool(name)


# The generated tool surface the agent personas draw from.
CONTEXT_TOOLS: dict[str, StructuredTool] = _ToolSurface(
    ContextRetriever().build_tools())
