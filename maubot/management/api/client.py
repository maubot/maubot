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
from json import JSONDecodeError

from aiohttp import web

from mautrix.types import UserID

from ...client import Client
from .base import routes
from .responses import ErrNotImplemented, ErrClientNotFound, ErrBodyNotJSON


@routes.get("/clients")
async def get_clients(request: web.Request) -> web.Response:
    return web.json_response([client.to_dict() for client in Client.cache.values()])


@routes.get("/client/{id}")
async def get_client(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return ErrClientNotFound
    return web.json_response(client.to_dict())


async def create_client(user_id: UserID, data: dict) -> web.Response:
    return ErrNotImplemented


async def update_client(client: Client, data: dict) -> web.Response:
    return ErrNotImplemented


@routes.put("/client/{id}")
async def update_client(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    try:
        data = await request.json()
    except JSONDecodeError:
        return ErrBodyNotJSON
    if not client:
        return await create_client(user_id, data)
    else:
        return await update_client(client, data)


@routes.delete("/client/{id}")
async def delete_client(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return ErrClientNotFound
    return ErrNotImplemented
