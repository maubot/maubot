# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2021 Tulir Asokan
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
import asyncio

from mautrix.util.program import Program

from .config import Config
from .db import init as init_db
from .server import MaubotServer
from .client import Client, init as init_client_class
from .loader.zip import init as init_zip_loader
from .instance import init as init_plugin_instance_class
from .management.api import init as init_mgmt_api
from .lib.future_awaitable import FutureAwaitable
from .__meta__ import __version__


class Maubot(Program):
    config: Config
    server: MaubotServer

    config_class = Config
    module = "maubot"
    name = "maubot"
    version = __version__
    command = "python -m maubot"
    description = "A plugin-based Matrix bot system."

    def prepare_log_websocket(self) -> None:
        from .management.api.log import init, stop_all
        init(self.loop)
        self.add_shutdown_actions(FutureAwaitable(stop_all))

    def prepare(self) -> None:
        super().prepare()

        if self.config["api_features.log"]:
            self.prepare_log_websocket()

        init_zip_loader(self.config)
        init_db(self.config)
        clients = init_client_class(self.config, self.loop)
        self.add_startup_actions(*(client.start() for client in clients))
        management_api = init_mgmt_api(self.config, self.loop)
        self.server = MaubotServer(management_api, self.config, self.loop)

        plugins = init_plugin_instance_class(self.config, self.server, self.loop)
        for plugin in plugins:
            plugin.load()

    async def start(self) -> None:
        if Client.crypto_db:
            self.log.debug("Starting client crypto database")
            await Client.crypto_db.start()
        await super().start()
        await self.server.start()

    async def stop(self) -> None:
        self.add_shutdown_actions(*(client.stop() for client in Client.cache.values()))
        await super().stop()
        self.log.debug("Stopping server")
        try:
            await asyncio.wait_for(self.server.stop(), 5)
        except asyncio.TimeoutError:
            self.log.warning("Stopping server timed out")


Maubot().run()
