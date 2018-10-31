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
import json

from . import routes, config, create_token
from .responses import ErrBadAuth, ErrBodyNotJSON


@routes.post("/login")
async def login(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return ErrBodyNotJSON
    secret = data.get("secret")
    if secret and config["server.unshared_secret"] == secret:
        user = data.get("user") or "root"
        return web.json_response({
            "token": create_token(user),
        })

    username = data.get("username")
    password = data.get("password")
    if config.check_password(username, password):
        return web.json_response({
            "token": create_token(username),
        })

    return ErrBadAuth
