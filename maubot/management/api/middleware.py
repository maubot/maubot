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
from typing import Awaitable, Callable
import base64
import logging

from aiohttp import web

from .auth import check_token
from .base import get_config
from .responses import resp

Handler = Callable[[web.Request], Awaitable[web.Response]]
log = logging.getLogger("maubot.server")


@web.middleware
async def auth(request: web.Request, handler: Handler) -> web.Response:
    subpath = request.path[len("/_matrix/maubot/v1") :]
    if (
        subpath.startswith("/auth/")
        or subpath.startswith("/client/auth_external_sso/complete/")
        or subpath == "/features"
        or subpath == "/logs"
    ):
        return await handler(request)
    err = check_token(request)
    if err is not None:
        return err
    return await handler(request)


@web.middleware
async def error(request: web.Request, handler: Handler) -> web.Response:
    try:
        return await handler(request)
    except web.HTTPException as ex:
        if ex.status_code == 404:
            return resp.path_not_found
        elif ex.status_code == 405:
            return resp.method_not_allowed
        return web.json_response(
            {
                "httpexception": {
                    "headers": {key: value for key, value in ex.headers.items()},
                    "class": type(ex).__name__,
                    "body": ex.text or base64.b64encode(ex.body),
                },
                "error": f"Unhandled HTTP {ex.status}: {ex.text[:128] or 'non-text response'}",
                "errcode": f"unhandled_http_{ex.status}",
            },
            status=ex.status,
        )
    except Exception:
        log.exception("Error in handler")
        return resp.internal_server_error


req_no = 0


def get_req_no():
    global req_no
    req_no += 1
    return req_no
