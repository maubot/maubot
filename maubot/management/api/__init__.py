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

from ...config import Config
from .base import routes, set_config
from .middleware import auth, error
from .auth import web as _
from .plugin import web as _
from .instance import web as _
from .client import web as _


def init(cfg: Config, loop: AbstractEventLoop) -> web.Application:
    set_config(cfg)
    app = web.Application(loop=loop, middlewares=[auth, error])
    app.add_routes(routes)
    return app
