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
from typing import Callable, Awaitable
from aiohttp import web

from .responses import ErrNoToken, ErrInvalidToken, ErrPathNotFound, ErrMethodNotAllowed
from .auth import is_valid_token

Handler = Callable[[web.Request], Awaitable[web.Response]]


@web.middleware
async def auth(request: web.Request, handler: Handler) -> web.Response:
    if "/auth/" in request.path:
        return await handler(request)
    token = request.headers.get("Authorization", "")
    if not token or not token.startswith("Bearer "):
        return ErrNoToken
    if not is_valid_token(token[len("Bearer "):]):
        return ErrInvalidToken
    return await handler(request)


@web.middleware
async def error(request: web.Request, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPException as ex:
        if ex.status_code == 404:
            return ErrPathNotFound
        elif ex.status_code == 405:
            return ErrMethodNotAllowed
        return web.json_response({
            "error": f"Unhandled HTTP {ex.status}",
            "errcode": f"unhandled_http_{ex.status}",
        }, status=ex.status)


req_no = 0


def get_req_no():
    global req_no
    req_no += 1
    return req_no
