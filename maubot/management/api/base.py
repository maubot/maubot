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
from __future__ import annotations

import asyncio

from aiohttp import web

from ...__meta__ import __version__
from ...config import Config

routes: web.RouteTableDef = web.RouteTableDef()
_config: Config | None = None


def set_config(config: Config) -> None:
    global _config
    _config = config


def get_config() -> Config:
    return _config


@routes.get("/version")
async def version(_: web.Request) -> web.Response:
    return web.json_response({"version": __version__})
