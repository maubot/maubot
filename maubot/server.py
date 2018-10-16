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
from aiohttp import web
import asyncio

from mautrix.api import PathBuilder

from .config import Config
from .__meta__ import __version__


class MaubotServer:
    def __init__(self, config: Config, loop: asyncio.AbstractEventLoop):
        self.loop = loop or asyncio.get_event_loop()
        self.app = web.Application(loop=self.loop)
        self.config = config

        path = PathBuilder(config["server.base_path"])
        self.app.router.add_get(path.version, self.version)

        as_path = PathBuilder(config["server.appservice_base_path"])
        self.app.router.add_put(as_path.transactions, self.handle_transaction)

        self.runner = web.AppRunner(self.app)

    async def start(self) -> None:
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.config["server.hostname"], self.config["server.port"])
        await site.start()

    async def stop(self) -> None:
        await self.runner.cleanup()

    @staticmethod
    async def version(_: web.Request) -> web.Response:
        return web.json_response({
            "version": __version__
        })

    async def handle_transaction(self, request: web.Request) -> web.Response:
        return web.Response(status=501)
