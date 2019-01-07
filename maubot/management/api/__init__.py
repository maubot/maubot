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
import importlib

from ...config import Config
from .base import routes, get_config, set_config, set_loop
from .auth import check_token
from .middleware import auth, error


@routes.get("/features")
def features(request: web.Request) -> web.Response:
    data = get_config()["api_features"]
    err = check_token(request)
    if err is None:
        return web.json_response(data)
    else:
        return web.json_response({
            "login": data["login"],
        })


def init(cfg: Config, loop: AbstractEventLoop) -> web.Application:
    set_config(cfg)
    set_loop(loop)
    for pkg, enabled in cfg["api_features"].items():
        if enabled:
            importlib.import_module(f"maubot.management.api.{pkg}")
    app = web.Application(loop=loop, middlewares=[auth, error], client_max_size=100 * 1024 * 1024)
    app.add_routes(routes)
    return app
