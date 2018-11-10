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
import logging
import asyncio

from aiohttp import web
from aiohttp.abc import AbstractAccessLogger

from mautrix.api import PathBuilder, Method

from .config import Config
from .__meta__ import __version__


class AccessLogger(AbstractAccessLogger):
    def log(self, request: web.Request, response: web.Response, time: int):
        self.logger.info(f'{request.remote} "{request.method} {request.path} '
                         f'{response.status} {response.body_length} '
                         f'in {round(time, 4)}s"')


class MaubotServer:
    log: logging.Logger = logging.getLogger("maubot.server")

    def __init__(self, config: Config, management: web.Application,
                 loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.app = web.Application(loop=self.loop)
        self.config = config

        path = PathBuilder(config["server.base_path"])
        self.add_route(Method.GET, path.version, self.version)
        self.app.add_subapp(config["server.base_path"], management)

        as_path = PathBuilder(config["server.appservice_base_path"])
        self.add_route(Method.PUT, as_path.transactions, self.handle_transaction)

        self.runner = web.AppRunner(self.app, access_log_class=AccessLogger)

    def add_route(self, method: Method, path: PathBuilder, handler) -> None:
        self.app.router.add_route(method.value, str(path), handler)

    async def start(self) -> None:
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.config["server.hostname"], self.config["server.port"])
        await site.start()
        self.log.info(f"Listening on {site.name}")

    async def stop(self) -> None:
        await self.runner.cleanup()

    @staticmethod
    async def version(_: web.Request) -> web.Response:
        return web.json_response({
            "version": __version__
        })

    async def handle_transaction(self, request: web.Request) -> web.Response:
        return web.Response(status=501)
