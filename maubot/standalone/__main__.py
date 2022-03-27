# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2022 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from typing import cast
import argparse
import asyncio
import copy
import importlib
import logging.config
import os.path
import signal
import sys

from aiohttp import ClientSession, hdrs, web
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from yarl import URL

from mautrix.types import (
    EventType,
    Filter,
    Membership,
    RoomEventFilter,
    RoomFilter,
    StrippedStateEvent,
)
from mautrix.util.async_db import Database, Scheme
from mautrix.util.config import BaseMissingError, RecursiveDict
from mautrix.util.logging import TraceLogger

from ..__meta__ import __version__
from ..loader import DatabaseType, PluginMeta
from ..matrix import MaubotMatrixClient
from ..plugin_base import Plugin
from ..plugin_server import PluginWebApp, PrefixResource
from ..server import AccessLogger
from .config import Config
from .database import NextBatch, upgrade_table
from .loader import FileSystemLoader

crypto_import_error = None

try:
    from mautrix.crypto import OlmMachine, PgCryptoStateStore, PgCryptoStore
except ImportError as err:
    crypto_import_error = err
    OlmMachine = PgCryptoStateStore = PgCryptoStore = None

parser = argparse.ArgumentParser(
    description="A plugin-based Matrix bot system -- standalone mode.",
    prog="python -m maubot.standalone",
)
parser.add_argument(
    "-c",
    "--config",
    type=str,
    default="config.yaml",
    metavar="<path>",
    help="the path to your config file",
)
parser.add_argument(
    "-b",
    "--base-config",
    type=str,
    default="pkg://maubot.standalone/example-config.yaml",
    metavar="<path>",
    help="the path to the example config (for automatic config updates)",
)
parser.add_argument(
    "-m",
    "--meta",
    type=str,
    default="maubot.yaml",
    metavar="<path>",
    help="the path to your plugin metadata file",
)
args = parser.parse_args()

config = Config(args.config, args.base_config)
config.load()
try:
    config.update()
except BaseMissingError:
    print("No example config found, not updating config")
except Exception as e:
    print("Failed to update config:", e)

logging.config.dictConfig(copy.deepcopy(config["logging"]))

log = logging.getLogger("maubot.init")

log.debug(f"Loading plugin metadata from {args.meta}")
yaml = YAML()
with open(args.meta, "r") as meta_file:
    meta: PluginMeta = PluginMeta.deserialize(yaml.load(meta_file.read()))

if "/" in meta.main_class:
    module, main_class = meta.main_class.split("/", 1)
else:
    module = meta.modules[0]
    main_class = meta.main_class
bot_module = importlib.import_module(module)
plugin: type[Plugin] = getattr(bot_module, main_class)
loader = FileSystemLoader(os.path.dirname(args.meta))

log.info(f"Initializing standalone {meta.id} v{meta.version} on maubot {__version__}")

db = Database.create(
    config["database"],
    db_args=config.get("database_opts", {}),
    ignore_foreign_tables=True,
    log=logging.getLogger("maubot.db.standalone.upgrade"),
    upgrade_table=upgrade_table,
)

user_id = config["user.credentials.id"]
device_id = config["user.credentials.device_id"]
homeserver = config["user.credentials.homeserver"]
access_token = config["user.credentials.access_token"]

crypto_store = state_store = None
if device_id and not OlmMachine:
    log.warning(
        "device_id set in config, but encryption dependencies not installed",
        exc_info=crypto_import_error,
    )
elif device_id:
    crypto_store = PgCryptoStore(account_id=user_id, pickle_key="mau.crypto", db=db)
    state_store = PgCryptoStateStore(db)

bot_config = None
if not meta.config and "base-config.yaml" in meta.extra_files:
    log.warning(
        "base-config.yaml in extra files, but config is not set to true. "
        "Assuming legacy plugin and loading config."
    )
    meta.config = True
if meta.config:
    log.debug("Loading config")
    config_class = plugin.get_config_class()

    def load() -> CommentedMap:
        return config["plugin_config"]

    def load_base() -> RecursiveDict[CommentedMap]:
        return RecursiveDict(config.load_base()["plugin_config"], CommentedMap)

    def save(data: RecursiveDict[CommentedMap]) -> None:
        config["plugin_config"] = data
        config.save()

    try:
        bot_config = config_class(load=load, load_base=load_base, save=save)
        bot_config.load_and_update()
    except Exception:
        log.fatal("Failed to load plugin config", exc_info=True)
        sys.exit(1)

if meta.webapp:
    web_app = web.Application()
    web_runner = web.AppRunner(web_app, access_log_class=AccessLogger)
    web_base_path = config["server.base_path"].rstrip("/")
    public_url = str(URL(config["server.public_url"]) / web_base_path.lstrip("/")).rstrip("/")
    plugin_webapp = PluginWebApp()

    async def _handle_plugin_request(req: web.Request) -> web.StreamResponse:
        if req.path.startswith(web_base_path):
            path_override = req.rel_url.path[len(web_base_path) :]
            url_override = req.rel_url.with_path(path_override).with_query(req.query_string)
            req = req.clone(rel_url=url_override)
            return await plugin_webapp.handle(req)
        return web.Response(status=404)

    resource = PrefixResource(web_base_path)
    resource.add_route(hdrs.METH_ANY, _handle_plugin_request)
    web_app.router.register_resource(resource)
else:
    web_app = web_runner = public_url = plugin_webapp = None

loop = asyncio.get_event_loop()

client: MaubotMatrixClient | None = None
bot: Plugin | None = None


async def main():
    http_client = ClientSession(loop=loop)

    global client, bot

    await db.start()
    nb = await NextBatch(db, user_id).load()

    client_log = logging.getLogger("maubot.client").getChild(user_id)
    client = MaubotMatrixClient(
        mxid=user_id,
        base_url=homeserver,
        token=access_token,
        client_session=http_client,
        loop=loop,
        log=client_log,
        sync_store=nb,
        state_store=state_store,
        device_id=device_id,
    )
    client.ignore_first_sync = config["user.ignore_first_sync"]
    client.ignore_initial_sync = config["user.ignore_initial_sync"]
    if crypto_store:
        await crypto_store.upgrade_table.upgrade(db)
        await state_store.upgrade_table.upgrade(db)
        await crypto_store.open()

        client.crypto = OlmMachine(client, crypto_store, state_store)
        crypto_device_id = await crypto_store.get_device_id()
        if crypto_device_id and crypto_device_id != device_id:
            log.fatal(
                "Mismatching device ID in crypto store and config "
                f"(store: {crypto_device_id}, config: {device_id})"
            )
            sys.exit(10)
        await client.crypto.load()
        if not crypto_device_id:
            await crypto_store.put_device_id(device_id)
        log.debug("Enabled encryption support")

    if web_runner:
        await web_runner.setup()
        site = web.TCPSite(web_runner, config["server.hostname"], config["server.port"])
        await site.start()
        log.info(f"Web server listening on {site.name}")

    while True:
        try:
            whoami = await client.whoami()
        except Exception as e:
            log.error(
                f"Failed to connect to homeserver: {type(e).__name__}: {e}"
                " - retrying in 10 seconds..."
            )
            await asyncio.sleep(10)
            continue
        if whoami.user_id != user_id:
            log.fatal(f"User ID mismatch: configured {user_id}, but server said {whoami.user_id}")
            sys.exit(11)
        elif whoami.device_id and device_id and whoami.device_id != device_id:
            log.fatal(
                f"Device ID mismatch: configured {device_id}, "
                f"but server said {whoami.device_id}"
            )
            sys.exit(12)
        log.debug(f"Confirmed connection as {whoami.user_id} / {whoami.device_id}")
        break

    if config["user.sync"]:
        if not nb.filter_id:
            filter_id = await client.create_filter(
                Filter(room=RoomFilter(timeline=RoomEventFilter(limit=50)))
            )
            await nb.put_filter_id(filter_id)
        _ = client.start(nb.filter_id)

    if config["user.autojoin"]:
        log.debug("Autojoin is enabled")

        @client.on(EventType.ROOM_MEMBER)
        async def _handle_invite(evt: StrippedStateEvent) -> None:
            if evt.state_key == client.mxid and evt.content.membership == Membership.INVITE:
                await client.join_room(evt.room_id)

    displayname, avatar_url = config["user.displayname"], config["user.avatar_url"]
    if avatar_url != "disable":
        await client.set_avatar_url(avatar_url)
    if displayname != "disable":
        await client.set_displayname(displayname)

    plugin_log = cast(TraceLogger, logging.getLogger("maubot.instance.__main__"))
    if meta.database:
        if meta.database_type == DatabaseType.SQLALCHEMY:
            import sqlalchemy as sql

            plugin_db = sql.create_engine(config["database"])
            if db.scheme == Scheme.SQLITE:
                log.warning(
                    "Using SQLite with legacy plugins in standalone mode can cause database "
                    "locking issues. Switching to Postgres or updating the plugin to use the "
                    "new asyncpg/aiosqlite database interface is recommended."
                )
        elif meta.database_type == DatabaseType.ASYNCPG:
            plugin_db = db
            upgrade_table = plugin.get_db_upgrade_table()
            if upgrade_table:
                await upgrade_table.upgrade(plugin_db)
        else:
            log.fatal(f"Unsupported database type {meta.database_type}")
            sys.exit(13)
    else:
        plugin_db = None
    bot = plugin(
        client=client,
        loop=loop,
        http=http_client,
        instance_id="__main__",
        log=plugin_log,
        config=bot_config,
        database=plugin_db,
        webapp=plugin_webapp,
        webapp_url=public_url,
        loader=loader,
    )

    await bot.internal_start()


async def stop(suppress_stop_error: bool = False) -> None:
    if client:
        client.stop()
    if bot:
        try:
            await bot.internal_stop()
        except Exception:
            if not suppress_stop_error:
                log.exception("Error stopping bot")
    if web_runner:
        await web_runner.shutdown()
        await web_runner.cleanup()
    await db.stop()


signal.signal(signal.SIGINT, signal.default_int_handler)
signal.signal(signal.SIGTERM, signal.default_int_handler)


try:
    log.info("Starting plugin")
    loop.run_until_complete(main())
except (Exception, KeyboardInterrupt) as e:
    if isinstance(e, KeyboardInterrupt):
        log.info("Startup interrupted, stopping")
    else:
        log.fatal("Failed to start plugin", exc_info=True)
    loop.run_until_complete(stop(suppress_stop_error=True))
    loop.close()
    sys.exit(1)

try:
    log.info("Startup completed, running forever")
    loop.run_forever()
except KeyboardInterrupt:
    log.info("Interrupt received, stopping")
    loop.run_until_complete(stop())
    loop.close()
    sys.exit(0)
except Exception:
    log.fatal("Fatal error in bot", exc_info=True)
    sys.exit(1)
