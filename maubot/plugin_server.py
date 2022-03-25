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

from typing import Awaitable, Callable
from functools import partial

from aiohttp import hdrs, web
from yarl import URL

Handler = Callable[[web.Request], Awaitable[web.Response]]
Middleware = Callable[[web.Request, Handler], Awaitable[web.Response]]


class PluginWebApp(web.UrlDispatcher):
    def __init__(self):
        super().__init__()
        self._middleware: list[Middleware] = []

    def add_middleware(self, middleware: Middleware) -> None:
        self._middleware.append(middleware)

    def remove_middleware(self, middleware: Middleware) -> None:
        self._middleware.remove(middleware)

    def clear(self) -> None:
        self._resources = []
        self._named_resources = {}
        self._middleware = []

    async def handle(self, request: web.Request) -> web.StreamResponse:
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
        assert not prefix or prefix.startswith("/"), prefix
        assert prefix in ("", "/") or not prefix.endswith("/"), prefix
        super().__init__(name=name)
        self._prefix = URL.build(path=prefix).raw_path

    @property
    def canonical(self):
        return self._prefix

    def get_info(self):
        return {"path": self._prefix}

    def url_for(self):
        return URL.build(path=self._prefix, encoded=True)

    def add_prefix(self, prefix):
        assert prefix.startswith("/")
        assert not prefix.endswith("/")
        assert len(prefix) > 1
        self._prefix = prefix + self._prefix

    def _match(self, path: str) -> dict:
        return {} if self.raw_match(path) else None

    def raw_match(self, path: str) -> bool:
        return path and path.startswith(self._prefix)
