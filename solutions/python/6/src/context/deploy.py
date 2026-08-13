"""Deploy the bank's semantic model to the Redis Context Retriever.

═══════════════════════════════════════════════════════════════════════
SECTION 4 - CONTEXT RETRIEVER: this file is an exercise file.
═══════════════════════════════════════════════════════════════════════

Run it from the Terminal panel once both Section 4 exercises are done
(the model in src/context/models.py, and the surface below):

    cd /workshop/code/python
    python -m src.context.deploy

Provided here: the guards, the client (extended to bind the surface to
YOUR Redis database), the model export, the bank's records, and the
reporting. The exercise is the heart of it — driving the
`redis-context-retriever` client to build the **context surface** (your
deployed model), mint the bot's scoped **agent key**, and import the
records through the service.

Requires CTX_ADMIN_KEY in .env (created on the console's Admin keys
page — Section 4, step 3; shown only once). CTX_API_URL / CTX_MCP_URL
default to the managed endpoints. (POST /api/context/deploy runs this
same function.)
"""

import asyncio
import json
import logging
from urllib.parse import urlparse

import redis

from src import config
from src.context import models

log = logging.getLogger("workshop")

SURFACE_NAME = "bank-iris-workshop"

_LOCAL_HOSTS = ("redis", "localhost", "127.0.0.1")


async def deploy() -> dict:
    if not config.CTX_ADMIN_KEY:
        return {"error": "CTX_ADMIN_KEY is not set — create an admin key "
                         "in the Redis Cloud console (Context Retriever -> "
                         "Admin keys), put it in .env, and re-run this "
                         "deploy."}
    if (urlparse(config.REDIS_URL).hostname or "") in _LOCAL_HOSTS:
        return {"error": "REDIS_URL points at a local or "
                         "container-internal Redis — there is no local "
                         "fallback; the managed Context Retriever "
                         "service can only reach your Redis Cloud "
                         "database. Fix REDIS_URL in .env (Getting "
                         "started, step 1) and re-run this deploy."}

    from context_surfaces.context_model import export_data_model

    # Provided: your ContextModel classes -> the deployable model
    # definition, and the bank's records built from the seed data.
    data_model = export_data_model(
        title=SURFACE_NAME,
        description="Customers, loans, and pre-approved offers for the "
                    "bank's WhatsApp servicing bot.",
        entities=models.BANK_ENTITIES,
    )
    gaps = _model_gaps(data_model)
    if gaps:
        return {"error": "The semantic model still has TODOs — finish the "
                         "indexing decisions in src/context/models.py "
                         "(Section 4, first exercise): " + "; ".join(gaps)}
    records = _bank_records()

    async with _client() as client:
        # ═══════════════════════════════════════════════════════════════
        # SECTION 4 - CONTEXT RETRIEVER (surface): build the context
        # surface. A context surface is simply your model, deployed:
        # hand the service the model, and it gives back retrieval tools
        # and a governed access point to the data. Three calls:
        #
        #   1. create_context_surface(...) — push the model to the
        #      service (the surface also carries the connection to YOUR
        #      database — built for you in _client below)
        #   2. create_agent_key(...) — mint the bot's scoped runtime
        #      credential (agents get a key, never database credentials)
        #   3. import_data(...) — the bank's records, one batch per
        #      entity, validated against your model on the way in
        #
        # Solved: the three calls are live below.
        # ═══════════════════════════════════════════════════════════════
        surface = await client.create_context_surface(
            config.CTX_ADMIN_KEY, SURFACE_NAME, data_model=data_model,
            description="Customers, loans, and pre-approved offers for "
                        "the bank's WhatsApp servicing bot")
        agent_key = await client.create_agent_key(
            config.CTX_ADMIN_KEY, surface.id, "wa-bot",
            description="Scoped key for the WhatsApp bot's agents")
        imported = [await client.import_data(config.CTX_ADMIN_KEY,
                                             surface.id, batch)
                    for batch in records.values()]
        return await _finish(client, surface, agent_key, imported, records)



def _model_gaps(data_model: dict) -> list[str]:
    """Provided: report the indexing decisions still missing from the
    model — the `# TODO` markers in src/context/models.py."""
    needed = {
        ("Loan", "lan"): ("key", "is_key_component=True"),
        ("Loan", "customer_id"): ("index", 'index="tag"'),
        ("Loan", "product"): ("index", 'index="tag"'),
        ("Loan", "status"): ("index", 'index="tag"'),
        ("Offer", "customer_id"): ("both",
                                   'is_key_component=True, index="tag"'),
        ("Offer", "product"): ("both",
                               'is_key_component=True, index="tag"'),
        ("Offer", "note"): ("index", 'index="text"'),
    }
    fields = {(entity["name"], field["name"]): field
              for entity in data_model.get("entities", [])
              for field in entity.get("fields", [])}
    gaps = []
    for (entity, name), (kind, fix) in needed.items():
        field = fields.get((entity, name))
        if field is None:
            gaps.append(f"{entity}.{name} is missing")
            continue
        no_key = kind in ("key", "both") and not field.get("is_key_component")
        no_index = kind in ("index", "both") and not field.get("redis_indices")
        if no_key or no_index:
            gaps.append(f"{entity}.{name} needs {fix}")
    # The reverse mistake: a TODO's arguments pasted onto the wrong field.
    for (entity, name), field in fields.items():
        if entity == "Customer" or (entity, name) in needed:
            continue
        if field.get("redis_indices") or field.get("is_key_component"):
            gaps.append(f"{entity}.{name} should not be indexed — did a "
                        "TODO land on the wrong field?")
    return gaps


def _client():
    """Provided: the official `redis-context-retriever` client, extended
    with one field its high-level wrapper doesn't expose yet — the
    surface's `data_source`, the embedded connection to YOUR Redis
    database. The admin API expects it at surface creation (it is what
    `ctxctl context-surface create --redis-addr ...` sends); the service
    stores and serves the imported rows through this connection."""
    from context_surfaces import UnifiedClient
    from context_surfaces.models import (CreateContextSurfaceRequest,
                                         DataSourceConnectionConfig,
                                         DataSourceRequest)

    class WorkshopClient(UnifiedClient):
        async def create_context_surface(self, admin_key, name,
                                         data_model=None, description=""):
            if not self._api_client:
                raise RuntimeError("Client not initialized. Use 'async "
                                   "with' context manager.")
            url = urlparse(config.REDIS_URL)
            return await self._api_client.create_context_surface(
                CreateContextSurfaceRequest(
                    name=name, description=description,
                    data_model=data_model,
                    data_source=DataSourceRequest(
                        type="redis",
                        connection_config=DataSourceConnectionConfig(
                            addr=f"{url.hostname}:{url.port or 6379}",
                            username=url.username or "default",
                            password=url.password or "",
                            tls_enabled=url.scheme == "rediss"))),
                admin_key=admin_key)

    return WorkshopClient()


async def _finish(client, surface, agent_key, imported,
                  records: dict) -> dict:
    """Provided: store the deployment so the agents' tool surface can find
    it, and report what the service generated."""
    _redis().hset(config.CTX_DEPLOYMENT_KEY, mapping={
        "surface_id": str(surface.id),
        "agent_key": agent_key.key,
    })
    tools = await client.list_tools(agent_key.key)
    return {
        "surface_id": str(surface.id),
        "records_imported": {entity: len(batch)
                             for entity, batch in records.items()},
        "import_result": [json.loads(r.model_dump_json())
                          if hasattr(r, "model_dump_json") else str(r)
                          for r in imported],
        "generated_tools": [t["name"] for t in tools],
        "next_step": "the agent key is stored — save any file in the Code "
                     "panel (or restart the api) so the agents pick up "
                     "the generated tools",
    }


def _redis() -> redis.Redis:
    return redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def _bank_records() -> dict[str, list]:
    """Provided: the bank's records from the seed data, grouped per
    entity — import_data validates each batch against a single entity's
    model, so a batch must hold records of one type."""
    dataset = json.loads((config.DATA_DIR / "customers.json").read_text())
    customers = [models.Customer(**{
        k: c[k] for k in models.Customer.model_fields if k in c})
        for c in dataset["customers"]]
    loans = [models.Loan(**{
        k: loan[k] for k in models.Loan.model_fields if k in loan})
        for loan in dataset["loans"]]
    offers = [models.Offer(customer_id=entry["customer_id"], **{
        k: offer[k] for k in models.Offer.model_fields if k in offer})
        for entry in dataset["offers"] for offer in entry["offers"]]
    return {"Customer": customers, "Loan": loans, "Offer": offers}


if __name__ == "__main__":
    print(json.dumps(asyncio.run(deploy()), indent=2, default=str))
