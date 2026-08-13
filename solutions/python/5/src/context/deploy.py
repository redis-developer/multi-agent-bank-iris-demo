"""Deploy the bank's semantic model to the Redis Context Retriever.

═══════════════════════════════════════════════════════════════════════
SECTION 4 - CONTEXT RETRIEVER: this file is an exercise file.    SOLVED.
═══════════════════════════════════════════════════════════════════════

Run it from the Terminal panel once both Section 4 exercises are done
(the model in src/context/models.py, and the surface below):

    cd /workshop/code/python
    python -m src.context.deploy

Provided here: the guards, the model export, the bank's records, and the
reporting. The exercise is the heart of it — driving the
`redis-context-retriever` client to build the **context surface** (your
deployed model), mint the bot's scoped **agent key**, and import the
records through the service.

Requires CTX_ADMIN_KEY in .env (from your Context Retriever service in
the Redis Cloud console). CTX_API_URL / CTX_MCP_URL default to the
managed endpoints. (POST /api/context/deploy runs this same function.)
"""

import asyncio
import json
import logging

import redis

from src import config
from src.context import models

log = logging.getLogger("workshop")

SURFACE_NAME = "bank-iris-workshop"


async def deploy() -> dict:
    if not config.CTX_ADMIN_KEY:
        return {"error": "CTX_ADMIN_KEY is not set — create the Context "
                         "Retriever service in the Redis Cloud console, put "
                         "its admin key in .env, and re-run this deploy."}
    if len(models.BANK_ENTITIES) < 3:
        return {"error": "The semantic model is incomplete — declare the "
                         "Loan and Offer entities in "
                         "src/context/models.py and add them to "
                         "BANK_ENTITIES (Section 4, first exercise)."}

    from context_surfaces import UnifiedClient
    from context_surfaces.context_model import export_data_model

    client = UnifiedClient()

    # Provided: your ContextModel classes -> the deployable model
    # definition, and the bank's records built from the seed data.
    data_model = export_data_model(
        title=SURFACE_NAME,
        description="Customers, loans, and pre-approved offers for the "
                    "bank's WhatsApp servicing bot.",
        entities=models.BANK_ENTITIES,
    )
    records = _bank_records()

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 4 - CONTEXT RETRIEVER (surface): build the context surface.
    #   1. create_context_surface(...) — deploy the model; the *surface*
    #      is the deployed model, the unit the service generates the
    #      retrieval tools from
    #   2. create_agent_key(...) — mint the bot's scoped runtime
    #      credential (agents get a key, never database credentials)
    #   3. import_data(...) — push the bank's records through the
    #      service, validated against your model on the way in
    # Finish with:  return await _finish(client, surface, agent_key,
    #                                    imported, len(records))
    # Solved.
    # ═══════════════════════════════════════════════════════════════════
    surface = await client.create_context_surface(
        config.CTX_ADMIN_KEY, SURFACE_NAME, data_model=data_model,
        description="Bank Iris workshop surface")
    agent_key = await client.create_agent_key(
        config.CTX_ADMIN_KEY, surface.id, "wa-bot",
        description="Scoped key for the WhatsApp bot's agents")
    imported = await client.import_data(config.CTX_ADMIN_KEY, surface.id,
                                        records)
    return await _finish(client, surface, agent_key, imported, len(records))


async def _finish(client, surface, agent_key, imported,
                  records_count: int) -> dict:
    """Provided: store the deployment so the agents' tool surface can find
    it, and report what the service generated."""
    _redis().hset(config.CTX_DEPLOYMENT_KEY, mapping={
        "surface_id": str(surface.id),
        "agent_key": agent_key.key,
    })
    tools = await client.list_tools(agent_key.key)
    return {
        "surface_id": str(surface.id),
        "records_imported": records_count,
        "import_result": json.loads(imported.model_dump_json())
        if hasattr(imported, "model_dump_json") else str(imported),
        "generated_tools": [t["name"] for t in tools],
        "next_step": "the agent key is stored — save any file in the Code "
                     "panel (or restart the api) so the agents pick up "
                     "the generated tools",
    }


def _redis() -> redis.Redis:
    return redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def _bank_records() -> list:
    """Provided: build ContextModel records from the workshop seed data."""
    dataset = json.loads((config.DATA_DIR / "customers.json").read_text())
    records: list = []
    for customer in dataset["customers"]:
        records.append(models.Customer(**{
            k: customer[k] for k in models.Customer.model_fields
            if k in customer}))
    for loan in dataset["loans"]:
        records.append(models.Loan(**{
            k: loan[k] for k in models.Loan.model_fields if k in loan}))
    for entry in dataset["offers"]:
        for offer in entry["offers"]:
            records.append(models.Offer(customer_id=entry["customer_id"], **{
                k: offer[k] for k in models.Offer.model_fields
                if k in offer}))
    return records


if __name__ == "__main__":
    print(json.dumps(asyncio.run(deploy()), indent=2, default=str))
