# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2021 Tulir Asokan
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
from typing import Dict, Tuple, NamedTuple, Optional
from json import JSONDecodeError
from http import HTTPStatus
import hashlib
import random
import string
import hmac

from aiohttp import web
from mautrix.api import SynapseAdminPath, Method
from mautrix.errors import MatrixRequestError
from mautrix.client import ClientAPI
from mautrix.types import LoginType

from .base import routes, get_config, get_loop
from .responses import resp


def known_homeservers() -> Dict[str, Dict[str, str]]:
    return get_config()["homeservers"]


@routes.get("/client/auth/servers")
async def get_known_servers(_: web.Request) -> web.Response:
    return web.json_response({key: value["url"] for key, value in known_homeservers().items()})


class AuthRequestInfo(NamedTuple):
    client: ClientAPI
    secret: str
    username: str
    password: str
    user_type: str


async def read_client_auth_request(request: web.Request) -> Tuple[Optional[AuthRequestInfo],
                                                                  Optional[web.Response]]:
    server_name = request.match_info.get("server", None)
    server = known_homeservers().get(server_name, None)
    if not server:
        return None, resp.server_not_found
    try:
        body = await request.json()
    except JSONDecodeError:
        return None, resp.body_not_json
    try:
        username = body["username"]
        password = body["password"]
    except KeyError:
        return None, resp.username_or_password_missing
    try:
        base_url = server["url"]
    except KeyError:
        return None, resp.invalid_server
    secret = server.get("secret")
    api = ClientAPI(base_url=base_url, loop=get_loop())
    user_type = body.get("user_type", "bot")
    return AuthRequestInfo(api, secret, username, password, user_type), None


def generate_mac(secret: str, nonce: str, user: str, password: str, admin: bool = False,
                 user_type: str = None) -> str:
    mac = hmac.new(key=secret.encode("utf-8"), digestmod=hashlib.sha1)
    mac.update(nonce.encode("utf-8"))
    mac.update(b"\x00")
    mac.update(user.encode("utf-8"))
    mac.update(b"\x00")
    mac.update(password.encode("utf-8"))
    mac.update(b"\x00")
    mac.update(b"admin" if admin else b"notadmin")
    if user_type is not None:
        mac.update(b"\x00")
        mac.update(user_type.encode("utf8"))
    return mac.hexdigest()


@routes.post("/client/auth/{server}/register")
async def register(request: web.Request) -> web.Response:
    info, err = await read_client_auth_request(request)
    if err is not None:
        return err
    client: ClientAPI
    client, secret, username, password, user_type = info
    if not secret:
        return resp.registration_secret_not_found
    path = SynapseAdminPath.v1.register
    res = await client.api.request(Method.GET, path)
    content = {
        "nonce": res["nonce"],
        "username": username,
        "password": password,
        "admin": False,
        "mac": generate_mac(secret, res["nonce"], username, password, user_type=user_type),
        "user_type": user_type,
    }
    try:
        return web.json_response(await client.api.request(Method.POST, path, content=content))
    except MatrixRequestError as e:
        return web.json_response({
            "errcode": e.errcode,
            "error": e.message,
            "http_status": e.http_status,
        }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@routes.post("/client/auth/{server}/login")
async def login(request: web.Request) -> web.Response:
    info, err = await read_client_auth_request(request)
    if err is not None:
        return err
    device_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    client = info.client
    try:
        res = await client.login(identifier=info.username, login_type=LoginType.PASSWORD,
                                 password=info.password, device_id=f"maubot_{device_id}",
                                 initial_device_display_name="Maubot", store_access_token=False)
        return web.json_response(res.serialize())
    except MatrixRequestError as e:
        return web.json_response({
            "errcode": e.errcode,
            "error": e.message,
        }, status=e.http_status)
