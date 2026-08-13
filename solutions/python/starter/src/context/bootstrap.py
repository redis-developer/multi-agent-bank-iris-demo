"""Bootstrap the Context Retriever: SDK login -> admin key -> .env.

PROVIDED — not an exercise file. Run once from the Terminal panel
(Section 4, step 3):

    cd /workshop/code/python
    python -m src.context.bootstrap

Everything the `redis-context-retriever` SDK can do, the workshop does
in SDK code — including the bootstrap the console page would do: log in
to Redis Cloud (the SDK's own auth service — email + password, the same
session your browser console holds), mint the **admin API key** through
the official client, and write `CTX_ADMIN_KEY` into `.env` (the api
hot-reloads it).

One caveat: accounts that sign in to Redis Cloud with Google/SSO have
no password for the direct login. Fallback: in the console, choose
**Context Retriever -> Create with CLI**, copy the admin key it shows
(once), and paste it into `.env` yourself.
"""

import asyncio
import getpass
import os
import re
import sys
from pathlib import Path

from dotenv import find_dotenv

from src import config

KEY_NAME = "bank-iris-workshop"


async def create_admin_key(email: str, password: str):
    """The SDK-only bootstrap: a Redis Cloud session login, then the
    admin key through the official API client — the same two calls the
    console (or `ctxctl auth login` + `ctxctl admin create`) makes."""
    from context_surfaces import UnifiedClient
    from context_surfaces.cli.services import SMAuthService
    from context_surfaces.client import ContextSurfacesClient
    from context_surfaces.models import CreateAdminKeyRequest

    session = await SMAuthService().login(email, password)
    api_url = UnifiedClient().api_url  # the client's own URL resolution
    async with ContextSurfacesClient(api_url) as api:
        return await api.create_admin_key(
            CreateAdminKeyRequest(
                name=KEY_NAME,
                description="Admin key for the bank Iris workshop"),
            session_id=session.jsessionid,
            csrf_token=session.csrf_token,
        )


def save_admin_key(key: str) -> Path | None:
    """Write CTX_ADMIN_KEY into .env in place. In place matters: .env is
    bind-mounted into the Code panel, and replacing the file (a new
    inode) would break that mount."""
    located = os.getenv("DOTENV_PATH") or find_dotenv()
    if not located:
        return None
    path = Path(located)
    if not path.is_file():
        return None
    text = path.read_text()
    line = f"CTX_ADMIN_KEY={key}"
    if re.search(r"^CTX_ADMIN_KEY=.*$", text, flags=re.M):
        text = re.sub(r"^CTX_ADMIN_KEY=.*$", line, text, flags=re.M)
    else:
        text = text + ("" if text.endswith("\n") else "\n") + line + "\n"
    try:
        with path.open("r+") as env_file:
            env_file.write(text)
            env_file.truncate()
    except OSError:
        return None
    return path


def main() -> int:
    if config.CTX_ADMIN_KEY:
        print("CTX_ADMIN_KEY is already set in .env — nothing to do.")
        print("(Clear the value and re-run to mint a fresh key.)")
        return 0

    print("Redis Cloud login — the SDK's direct login. (Google/SSO "
          "accounts have no password: use the console fallback in the "
          "docs instead.)")
    email = input("  email: ").strip()
    password = getpass.getpass("  password (hidden): ")

    try:
        admin_key = asyncio.run(create_admin_key(email, password))
    except Exception as error:
        print(f"\nBootstrap failed: {error}")
        print("If your account signs in with Google/SSO, mint the key in "
              "the console instead (Context Retriever -> Create with "
              "CLI) and paste it into .env as CTX_ADMIN_KEY.")
        return 1

    print(f"\nAdmin key created: {admin_key.name} (owner {admin_key.owner})")
    saved = save_admin_key(admin_key.key)
    if saved:
        print(f"CTX_ADMIN_KEY written to {saved} — the api reloads .env "
              "within a few seconds. Next: the Section 4 exercises "
              "(src/context/models.py, then python -m src.context.deploy).")
    else:
        print("Could not write .env — add this line yourself in the Code "
              "panel (the key is shown only here):")
        print(f"  CTX_ADMIN_KEY={admin_key.key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
