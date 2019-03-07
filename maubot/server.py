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
from typing import Tuple, List, Dict, Callable, Awaitable
from functools import partial
import logging
import asyncio

from aiohttp import web, hdrs, URL
from aiohttp.abc import AbstractAccessLogger
import pkg_resources

from mautrix.api import PathBuilder, Method

from .config import Config
from .__meta__ import __version__


class AccessLogger(AbstractAccessLogger):
    def log(self, request: web.Request, response: web.Response, time: int):
        self.logger.info(f'{request.remote} "{request.method} {request.path} '
                         f'{response.status} {response.body_length} '
                         f'in {round(time, 4)}s"')


Handler = Callable[[web.Request], Awaitable[web.Response]]
Middleware = Callable[[web.Request, Handler], Awaitable[web.Response]]


class PluginWebApp(web.UrlDispatcher):
    def __init__(self):
        super().__init__()
        self._middleware: List[Middleware] = []

    def add_middleware(self, middleware: Middleware) -> None:
        self._middleware.append(middleware)

    def remove_middleware(self, middleware: Middleware) -> None:
        self._middleware.remove(middleware)

    async def handle(self, request: web.Request) -> web.Response:
        match_info = await self.resolve(request)
        match_info.freeze()
        resp = None
        request._match_info = match_info
        expect = request.headers.get(hdrs.EXPECT)
        if expect:
            resp = await match_info.expect_handler(request)
            await request.writer.drain()
        if resp is None:
            handler = match_info.handler
            for middleware in self._middleware:
                handler = partial(middleware, handler=handler)
            resp = await handler(request)
        return resp


class PrefixResource(web.Resource):
    def __init__(self, prefix, *, name=None):
        assert not prefix or prefix.startswith('/'), prefix
        assert prefix in ('', '/') or not prefix.endswith('/'), prefix
        super().__init__(name=name)
        self._prefix = URL.build(path=prefix).raw_path

    @property
    def canonical(self):
        return self._prefix

    def add_prefix(self, prefix):
        assert prefix.startswith('/')
        assert not prefix.endswith('/')
        assert len(prefix) > 1
        self._prefix = prefix + self._prefix

    def _match(self, path: str) -> dict:
        return {} if self.raw_match(path) else None

    def raw_match(self, path: str) -> bool:
        return path and path.startswith(self._prefix)


class MaubotServer:
    log: logging.Logger = logging.getLogger("maubot.server")

    def __init__(self, config: Config, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.app = web.Application(loop=self.loop, client_max_size=100 * 1024 * 1024)
        self.config = config

        as_path = PathBuilder(config["server.appservice_base_path"])
        self.add_route(Method.PUT, as_path.transactions, self.handle_transaction)

        self.plugin_routes: Dict[str, PluginWebApp] = {}
        resource = PrefixResource(config["server.plugin_base_path"])
        resource.add_route(hdrs.METH_ANY, self.handle_plugin_path)
        self.app.router.register_resource(resource)

        self.setup_management_ui()

        self.runner = web.AppRunner(self.app, access_log_class=AccessLogger)

    async def handle_plugin_path(self, request: web.Request) -> web.Response:
        for path, app in self.plugin_routes.items():
            if request.path.startswith(path):
                request = request.clone(rel_url=request.path[len(path):])
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
            self.plugin_routes.pop(subpath)
        except KeyError:
            return

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
