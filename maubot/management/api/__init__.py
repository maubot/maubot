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
from .base import routes, set_config, set_loop
from .middleware import auth, error
from .auth import web as _
from .plugin import web as _
from .instance import web as _
from .client import web as _
from .dev_open import web as _
from .log import stop_all as stop_log_sockets, init as init_log_listener


def init(cfg: Config, loop: AbstractEventLoop) -> web.Application:
    set_config(cfg)
    set_loop(loop)
    app = web.Application(loop=loop, middlewares=[auth, error])
    app.add_routes(routes)
    return app


async def stop() -> None:
    await stop_log_sockets()
