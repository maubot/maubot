# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2018 Tulir Asokan
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
from sqlalchemy import orm
import sqlalchemy as sql
import logging.config
import argparse
import asyncio
import copy
import sys
import signal

from .config import Config
from .db import Base, init as init_db
from .server import MaubotServer
from .client import Client, init as init_client
from .loader import ZippedPluginLoader
from .plugin import PluginInstance
from .__meta__ import __version__

parser = argparse.ArgumentParser(description="A plugin-based Matrix bot system.",
                                 prog="python -m maubot")
parser.add_argument("-c", "--config", type=str, default="config.yaml",
                    metavar="<path>", help="the path to your config file")
parser.add_argument("-b", "--base-config", type=str, default="example-config.yaml",
                    metavar="<path>", help="the path to the example config "
                                           "(for automatic config updates)")
args = parser.parse_args()

config = Config(args.config, args.base_config)
config.load()
config.update()

logging.config.dictConfig(copy.deepcopy(config["logging"]))
log = logging.getLogger("maubot.init")
log.debug(f"Initializing maubot {__version__}")

db_engine: sql.engine.Engine = sql.create_engine(config["database"])
db_factory = orm.sessionmaker(bind=db_engine)
db_session = orm.scoping.scoped_session(db_factory)
Base.metadata.bind = db_engine
Base.metadata.create_all()

loop = asyncio.get_event_loop()

init_db(db_session)
init_client(loop)
server = MaubotServer(config, loop)
ZippedPluginLoader.load_all(*config["plugin_directories"])
plugins = PluginInstance.all()

for plugin in plugins:
    plugin.load()

signal.signal(signal.SIGINT, signal.default_int_handler)
signal.signal(signal.SIGTERM, signal.default_int_handler)

try:
    loop.run_until_complete(asyncio.gather(
        server.start(),
        *[plugin.start() for plugin in plugins]))
    log.debug("Startup actions complete, running forever")
    loop.run_forever()
except KeyboardInterrupt:
    log.debug("Interrupt received, stopping HTTP clients/servers and saving database")
    for client in Client.cache.values():
        client.stop()
    db_session.commit()
    loop.run_until_complete(server.stop())
    log.debug("Everything stopped, shutting down")
    sys.exit(0)
