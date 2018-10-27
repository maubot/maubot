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
from asyncio import AbstractEventLoop

from mautrix.types import UserID
from mautrix.util.signed_token import sign_token, verify_token

from ...config import Config

routes = web.RouteTableDef()
config: Config = None


def is_valid_token(token: str) -> bool:
    data = verify_token(config["server.unshared_secret"], token)
    user_id = data.get("user_id", None)
    return user_id is not None and user_id in config["admins"]


def create_token(user: UserID) -> str:
    return sign_token(config["server.unshared_secret"], {
        "user_id": user,
    })


def init(cfg: Config, loop: AbstractEventLoop) -> web.Application:
    global config
    config = cfg
    from .middleware import auth, error, log
    app = web.Application(loop=loop, middlewares=[auth, log, error])
    app.add_routes(routes)
    return app
