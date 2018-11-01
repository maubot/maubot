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
from time import time
import json

from aiohttp import web

from mautrix.types import UserID
from mautrix.util.signed_token import sign_token, verify_token

from .base import routes, get_config
from .responses import ErrBadAuth, ErrBodyNotJSON


def is_valid_token(token: str) -> bool:
    data = verify_token(get_config()["server.unshared_secret"], token)
    if not data:
        return False
    return get_config().is_admin(data.get("user_id", None))


def create_token(user: UserID) -> str:
    return sign_token(get_config()["server.unshared_secret"], {
        "user_id": user,
    })


@routes.post("/login")
async def login(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return ErrBodyNotJSON
    secret = data.get("secret")
    if secret and get_config()["server.unshared_secret"] == secret:
        user = data.get("user") or "root"
        return web.json_response({
            "token": create_token(user),
            "created_at": int(time()),
        })

    username = data.get("username")
    password = data.get("password")
    if get_config().check_password(username, password):
        return web.json_response({
            "token": create_token(username),
            "created_at": int(time()),
        })

    return ErrBadAuth
