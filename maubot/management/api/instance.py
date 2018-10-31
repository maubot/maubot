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
from json import JSONDecodeError

from mautrix.types import UserID

from ...db import DBClient
from ...client import Client
from .base import routes
from .responses import ErrNotImplemented, ErrClientNotFound, ErrBodyNotJSON


@routes.get("/instances")
async def get_instances(_: web.Request) -> web.Response:
    return web.json_response([client.to_dict() for client in Client.cache.values()])


@routes.get("/instance/{id}")
async def get_instance(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return ErrClientNotFound
    return web.json_response(client.to_dict())


async def create_instance(user_id: UserID, data: dict) -> web.Response:
    return ErrNotImplemented


async def update_instance(client: Client, data: dict) -> web.Response:
    return ErrNotImplemented


@routes.put("/instance/{id}")
async def update_instance(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    try:
        data = await request.json()
    except JSONDecodeError:
        return ErrBodyNotJSON
    if not client:
        return await create_instance(user_id, data)
    else:
        return await update_instance(client, data)


@routes.delete("/instance/{id}")
async def delete_instance(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return ErrClientNotFound
    return ErrNotImplemented
