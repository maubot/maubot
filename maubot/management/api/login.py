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
import json

from aiohttp import web

from .base import routes, get_config
from .responses import resp
from .auth import create_token

@routes.post("/auth/login")
async def login(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return resp.body_not_json
    secret = data.get("secret")
    if secret and get_config()["server.unshared_secret"] == secret:
        user = data.get("user") or "root"
        return resp.logged_in(create_token(user))

    username = data.get("username")
    password = data.get("password")
    if get_config().check_password(username, password):
        return resp.logged_in(create_token(username))

    return resp.bad_auth
