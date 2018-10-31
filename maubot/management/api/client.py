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

from .base import routes
from .responses import ErrNotImplemented


@routes.get("/clients")
def get_clients(request: web.Request) -> web.Response:
    return ErrNotImplemented


@routes.get("/client/{id}")
def get_client(request: web.Request) -> web.Response:
    return ErrNotImplemented


@routes.put("/client/{id}")
def update_client(request: web.Request) -> web.Response:
    return ErrNotImplemented


@routes.delete("/client/{id}")
def delete_client(request: web.Request) -> web.Response:
    return ErrNotImplemented
