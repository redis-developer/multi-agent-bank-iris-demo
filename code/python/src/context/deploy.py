"""Deploy the bank's semantic model to the Redis Context Retriever.

PROVIDED — not an exercise file. Run it yourself from the Terminal panel
once the Section 4 exercise (src/context/models.py) is complete:

    cd /workshop/code/python
    python -m src.context.deploy

It drives the `redis-context-retriever` Python client end to end:

  1. exports the data model from BANK_ENTITIES,
  2. creates a context surface on the service,
  3. mints a scoped agent key for the bot,
  4. imports the bank's records through the service, and
  5. stores the surface id + agent key in the workshop Redis so the
     agents' tool surface (src/context/retriever.py) can find them.

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
                         "BANK_ENTITIES (Section 4 exercise)."}

    from context_surfaces import UnifiedClient
    from context_surfaces.context_model import export_data_model

    client = UnifiedClient()

    data_model = export_data_model(
        title=SURFACE_NAME,
        description="Customers, loans, and pre-approved offers for the "
                    "bank's WhatsApp servicing bot.",
        entities=models.BANK_ENTITIES,
    )
    surface = await client.create_context_surface(
        config.CTX_ADMIN_KEY, SURFACE_NAME, data_model=data_model,
        description="Bank Iris workshop surface")
    agent_key = await client.create_agent_key(
        config.CTX_ADMIN_KEY, surface.id, "wa-bot",
        description="Scoped key for the WhatsApp bot's agents")

    records = _bank_records()
    imported = await client.import_data(config.CTX_ADMIN_KEY, surface.id,
                                        records)

    _redis().hset(config.CTX_DEPLOYMENT_KEY, mapping={
        "surface_id": str(surface.id),
        "agent_key": agent_key.key,
    })

    tools = await client.list_tools(agent_key.key)
    return {
        "surface_id": str(surface.id),
        "records_imported": len(records),
        "import_result": json.loads(imported.model_dump_json())
        if hasattr(imported, "model_dump_json") else str(imported),
        "generated_tools": [t["name"] for t in tools],
        "next_step": "the agent key is stored — restart the api (or save "
                     "any file in the Code panel) so the agents pick up "
                     "the generated tools",
    }


def _redis() -> redis.Redis:
    return redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def _bank_records() -> list:
    """Build ContextModel records from the workshop seed data."""
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
