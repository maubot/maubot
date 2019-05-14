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
from typing import Callable, Any, Awaitable

from aiohttp import web, hdrs

WebHandler = Callable[[web.Request], Awaitable[web.StreamResponse]]
WebHandlerDecorator = Callable[[WebHandler], WebHandler]


def head(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_HEAD, path, **kwargs)


def options(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_OPTIONS, path, **kwargs)


def get(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_GET, path, **kwargs)


def post(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_POST, path, **kwargs)


def put(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_PUT, path, **kwargs)


def patch(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_PATCH, path, **kwargs)


def delete(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_DELETE, path, **kwargs)


def view(path: str, **kwargs: Any) -> WebHandlerDecorator:
    return handle(hdrs.METH_ANY, path, **kwargs)


def handle(method: str, path: str, **kwargs) -> WebHandlerDecorator:
    def decorator(handler: WebHandler) -> WebHandler:
        try:
            handlers = getattr(handler, "__mb_web_handler__")
        except AttributeError:
            handlers = []
            setattr(handler, "__mb_web_handler__", handlers)
        handlers.append((method, path, kwargs))
        return handler

    return decorator
