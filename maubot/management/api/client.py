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
from typing import Optional
from json import JSONDecodeError
from http import HTTPStatus

from aiohttp import web

from mautrix.types import UserID, SyncToken, FilterID
from mautrix.errors import MatrixRequestError, MatrixConnectionError, MatrixInvalidToken
from mautrix.client import Client as MatrixClient

from ...db import DBClient
from ...client import Client
from .base import routes
from .responses import resp


@routes.get("/clients")
async def get_clients(_: web.Request) -> web.Response:
    return resp.found([client.to_dict() for client in Client.cache.values()])


@routes.get("/client/{id}")
async def get_client(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return resp.client_not_found
    return resp.found(client.to_dict())


async def _create_client(user_id: Optional[UserID], data: dict) -> web.Response:
    homeserver = data.get("homeserver", None)
    access_token = data.get("access_token", None)
    new_client = MatrixClient(mxid="@not:a.mxid", base_url=homeserver, token=access_token,
                              loop=Client.loop, client_session=Client.http_client)
    try:
        mxid = await new_client.whoami()
    except MatrixInvalidToken:
        return resp.bad_client_access_token
    except MatrixRequestError:
        return resp.bad_client_access_details
    except MatrixConnectionError:
        return resp.bad_client_connection_details
    if user_id is None:
        existing_client = Client.get(mxid, None)
        if existing_client is not None:
            return resp.user_exists
    elif mxid != user_id:
        return resp.mxid_mismatch(mxid)
    db_instance = DBClient(id=mxid, homeserver=homeserver, access_token=access_token,
                           enabled=data.get("enabled", True), next_batch=SyncToken(""),
                           filter_id=FilterID(""), sync=data.get("sync", True),
                           autojoin=data.get("autojoin", True),
                           displayname=data.get("displayname", ""),
                           avatar_url=data.get("avatar_url", ""))
    client = Client(db_instance)
    Client.db.add(db_instance)
    Client.db.commit()
    await client.start()
    return resp.created(client.to_dict())


async def _update_client(client: Client, data: dict) -> web.Response:
    try:
        await client.update_access_details(data.get("access_token", None),
                                           data.get("homeserver", None))
    except MatrixInvalidToken:
        return resp.bad_client_access_token
    except MatrixRequestError:
        return resp.bad_client_access_details
    except MatrixConnectionError:
        return resp.bad_client_connection_details
    except ValueError as e:
        return resp.mxid_mismatch(str(e)[len("MXID mismatch: "):])
    await client.update_avatar_url(data.get("avatar_url", None))
    await client.update_displayname(data.get("displayname", None))
    await client.update_started(data.get("started", None))
    client.enabled = data.get("enabled", client.enabled)
    client.autojoin = data.get("autojoin", client.autojoin)
    client.sync = data.get("sync", client.sync)
    return resp.updated(client.to_dict())


@routes.post("/client/new")
async def create_client(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except JSONDecodeError:
        return resp.body_not_json
    return await _create_client(None, data)


@routes.put("/client/{id}")
async def update_client(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    try:
        data = await request.json()
    except JSONDecodeError:
        return resp.body_not_json
    if not client:
        return await _create_client(user_id, data)
    else:
        return await _update_client(client, data)


@routes.delete("/client/{id}")
async def delete_client(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return resp.client_not_found
    if len(client.references) > 0:
        return resp.client_in_use
    if client.started:
        await client.stop()
    client.delete()
    return resp.deleted


@routes.post("/client/{id}/avatar")
async def upload_avatar(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return resp.client_not_found
    content = await request.read()
    return web.json_response({
        "content_uri": await client.client.upload_media(
            content, request.headers.get("Content-Type", None)),
    })


@routes.get("/client/{id}/avatar")
async def download_avatar(request: web.Request) -> web.Response:
    user_id = request.match_info.get("id", None)
    client = Client.get(user_id, None)
    if not client:
        return resp.client_not_found
    if not client.avatar_url or client.avatar_url == "disable":
        return web.Response()
    return web.Response(body=await client.client.download_media(client.avatar_url))
