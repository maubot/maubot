# maubot - A plugin-based Matrix bot system.
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
from typing import Tuple, Dict
import logging
import asyncio
import json
from yarl import URL

from aiohttp import web, hdrs
from aiohttp.abc import AbstractAccessLogger
import pkg_resources

from mautrix.api import PathBuilder, Method

from .config import Config
from .plugin_server import PrefixResource, PluginWebApp
from .__meta__ import __version__


class AccessLogger(AbstractAccessLogger):
    def log(self, request: web.Request, response: web.Response, time: int):
        self.logger.info(f'{request.remote} "{request.method} {request.path} '
                         f'{response.status} {response.body_length} '
                         f'in {round(time, 4)}s"')


class MaubotServer:
    log: logging.Logger = logging.getLogger("maubot.server")
    plugin_routes: Dict[str, PluginWebApp]

    def __init__(self, management_api: web.Application, config: Config,
                 loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.app = web.Application(loop=self.loop, client_max_size=100 * 1024 * 1024)
        self.config = config

        self.setup_appservice()
        self.app.add_subapp(config["server.base_path"], management_api)
        self.setup_instance_subapps()
        self.setup_management_ui()

        self.runner = web.AppRunner(self.app, access_log_class=AccessLogger)

    async def handle_plugin_path(self, request: web.Request) -> web.Response:
        for path, app in self.plugin_routes.items():
            if request.path.startswith(path):
                request = request.clone(rel_url=request.rel_url
                                        .with_path(request.rel_url.path[len(path):])
                                        .with_query(request.query_string))
                return await app.handle(request)
        return web.Response(status=404)

    def get_instance_subapp(self, instance_id: str) -> Tuple[PluginWebApp, str]:
        subpath = self.config["server.plugin_base_path"] + instance_id
        url = self.config["server.public_url"] + subpath
        try:
            return self.plugin_routes[subpath], url
        except KeyError:
            app = PluginWebApp()
            self.plugin_routes[subpath] = app
            return app, url

    def remove_instance_webapp(self, instance_id: str) -> None:
        try:
            subpath = self.config["server.plugin_base_path"] + instance_id
            self.plugin_routes.pop(subpath).clear()
        except KeyError:
            return

    def setup_instance_subapps(self) -> None:
        self.plugin_routes = {}
        resource = PrefixResource(self.config["server.plugin_base_path"].rstrip("/"))
        resource.add_route(hdrs.METH_ANY, self.handle_plugin_path)
        self.app.router.register_resource(resource)

    def setup_appservice(self) -> None:
        as_path = PathBuilder(self.config["server.appservice_base_path"])
        self.add_route(Method.PUT, as_path.transactions, self.handle_transaction)

    def setup_management_ui(self) -> None:
        ui_base = self.config["server.ui_base_path"]
        if ui_base == "/":
            ui_base = ""
        directory = (self.config["server.override_resource_path"]
                     or pkg_resources.resource_filename("maubot", "management/frontend/build"))
        self.app.router.add_static(f"{ui_base}/static", f"{directory}/static")
        self.setup_static_root_files(directory, ui_base)

        with open(f"{directory}/index.html", "r") as file:
            index_html = file.read()

        @web.middleware
        async def frontend_404_middleware(request: web.Request, handler) -> web.Response:
            if hasattr(handler, "__self__") and isinstance(handler.__self__, web.StaticResource):
                try:
                    return await handler(request)
                except web.HTTPNotFound:
                    return web.Response(body=index_html, content_type="text/html")
            return await handler(request)

        async def ui_base_redirect(_: web.Request) -> web.Response:
            raise web.HTTPFound(f"{ui_base}/")

        self.app.middlewares.append(frontend_404_middleware)
        self.app.router.add_get(f"{ui_base}/", lambda _: web.Response(body=index_html,
                                                                      content_type="text/html"))
        self.app.router.add_get(ui_base, ui_base_redirect)

    def setup_static_root_files(self, directory: str, ui_base: str) -> None:
        files = {
            "asset-manifest.json": "application/json",
            "manifest.json": "application/json",
            "favicon.png": "image/png",
        }
        for file, mime in files.items():
            with open(f"{directory}/{file}", "rb") as stream:
                data = stream.read()
            self.app.router.add_get(f"{ui_base}/{file}", lambda _: web.Response(body=data,
                                                                                content_type=mime))

        # also set up a resource path for the public url path prefix config
        # cut the prefix path from public_url
        public_url = self.config["server.public_url"]
        base_path = self.config["server.base_path"]
        public_url_path = ""
        if public_url:
            public_url_path = URL(public_url).path.rstrip("/")

        # assemble with base_path
        api_path = f"{public_url_path}{base_path}"

        path_prefix_response_body = json.dumps({"api_path": api_path.rstrip("/")})
        self.app.router.add_get(f"{ui_base}/paths.json", lambda _: web.Response(body=path_prefix_response_body,
                                                                                content_type="application/json"))

    def add_route(self, method: Method, path: PathBuilder, handler) -> None:
        self.app.router.add_route(method.value, str(path), handler)

    async def start(self) -> None:
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.config["server.hostname"], self.config["server.port"])
        await site.start()
        self.log.info(f"Listening on {site.name}")

    async def stop(self) -> None:
        await self.runner.shutdown()
        await self.runner.cleanup()

    @staticmethod
    async def version(_: web.Request) -> web.Response:
        return web.json_response({
            "version": __version__
        })

    async def handle_transaction(self, request: web.Request) -> web.Response:
        return web.Response(status=501)
