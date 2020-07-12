# supportportal - A maubot plugin to manage customer support on Matrix.
# Copyright (C) 2019 Tulir Asokan
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
from typing import Optional
from aiohttp import ClientSession
import logging.config
import importlib
import argparse
import asyncio
import signal
import copy
import sys

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import sqlalchemy as sql

from mautrix.util.config import RecursiveDict
from mautrix.util.db import Base
from mautrix.types import (UserID, Filter, RoomFilter, RoomEventFilter, StrippedStateEvent,
                           EventType, Membership)

from .config import Config
from ..plugin_base import Plugin
from ..loader import PluginMeta
from ..matrix import MaubotMatrixClient
from ..lib.store_proxy import SyncStoreProxy
from ..__meta__ import __version__

parser = argparse.ArgumentParser(
    description="A plugin-based Matrix bot system -- standalone mode.",
    prog="python -m maubot.standalone")
parser.add_argument("-c", "--config", type=str, default="config.yaml",
                    metavar="<path>", help="the path to your config file")
parser.add_argument("-b", "--base-config", type=str, default="example-config.yaml",
                    metavar="<path>", help="the path to the example config "
                                           "(for automatic config updates)")
parser.add_argument("-m", "--meta", type=str, default="maubot.yaml",
                    metavar="<path>", help="the path to your plugin metadata file")
args = parser.parse_args()

config = Config(args.config, args.base_config)
config.load()
try:
    config.update()
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
plugin = getattr(bot_module, main_class)

log.info(f"Initializing standalone {meta.id} v{meta.version} on maubot {__version__}")


class NextBatch(Base):
    __tablename__ = "standalone_next_batch"

    user_id: str = sql.Column(sql.String(255), primary_key=True)
    next_batch: str = sql.Column(sql.String(255))
    filter_id: str = sql.Column(sql.String(255))

    @classmethod
    def get(cls, user_id: UserID) -> Optional['NextBatch']:
        return cls._select_one_or_none(cls.c.user_id == user_id)


log.debug("Opening database")
db = sql.create_engine(config["database"])
Base.metadata.bind = db
Base.metadata.create_all()
NextBatch.bind(db)

user_id = config["user.credentials.id"]
homeserver = config["user.credentials.homeserver"]
access_token = config["user.credentials.access_token"]

nb = NextBatch.get(user_id)
if not nb:
    nb = NextBatch(user_id=user_id, next_batch="", filter_id="")
    nb.insert()

bot_config = None
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

loop = asyncio.get_event_loop()

client: MaubotMatrixClient = None
bot: Plugin = None


async def main():
    http_client = ClientSession(loop=loop)

    global client, bot

    client = MaubotMatrixClient(mxid=user_id, base_url=homeserver, token=access_token,
                                client_session=http_client, loop=loop, store=SyncStoreProxy(nb),
                                log=logging.getLogger("maubot.client").getChild(user_id))

    while True:
        try:
            whoami_user_id = await client.whoami()
        except Exception:
            log.exception("Failed to connect to homeserver, retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue
        if whoami_user_id != user_id:
            log.fatal(f"User ID mismatch: configured {user_id}, but server said {whoami_user_id}")
            sys.exit(1)
        break

    if config["user.sync"]:
        if not nb.filter_id:
            nb.edit(filter_id=await client.create_filter(Filter(
                room=RoomFilter(timeline=RoomEventFilter(limit=50)),
            )))
        client.start(nb.filter_id)

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

    bot = plugin(client=client, loop=loop, http=http_client, instance_id="__main__",
                 log=logging.getLogger("maubot.instance.__main__"), config=bot_config,
                 database=db if meta.database else None, webapp=None, webapp_url=None)

    await bot.internal_start()


try:
    log.info("Starting plugin")
    loop.run_until_complete(main())
except Exception:
    log.fatal("Failed to start plugin", exc_info=True)
    sys.exit(1)

signal.signal(signal.SIGINT, signal.default_int_handler)
signal.signal(signal.SIGTERM, signal.default_int_handler)

try:
    log.info("Startup completed, running forever")
    loop.run_forever()
except KeyboardInterrupt:
    log.info("Interrupt received, stopping")
    client.stop()
    loop.run_until_complete(bot.internal_stop())
    loop.close()
    sys.exit(0)
except Exception:
    log.fatal("Fatal error in bot", exc_info=True)
    sys.exit(1)
