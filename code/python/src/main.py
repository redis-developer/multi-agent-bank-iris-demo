"""WhatsApp banking bot — FastAPI entrypoint.

On startup: seed Redis with the workshop dataset (idempotent), then build
the chat pipeline. Restart the api container after `./solve` or code edits
outside --reload's view: `docker compose restart api`.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.chat.service import ChatService
from src.data import loader

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("workshop")


@asynccontextmanager
async def lifespan(app: FastAPI):
    summary = loader.ensure_loaded()
    if summary["skipped"]:
        log.info("Dataset already loaded — skipping seed.")
    else:
        log.info("Seeded dataset: %s", summary)
    app.state.chat_service = ChatService()
    log.info("Chat pipeline ready.")
    yield


app = FastAPI(title="Multi-agent bank WhatsApp bot", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])
app.include_router(router)
