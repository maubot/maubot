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
from mautrix.types import LoginType, LoginResponse

from .base import routes, get_config, get_loop
from .responses import resp
from .client import _create_or_update_client, _create_client


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
    device_name: str
    update_client: bool


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
    return AuthRequestInfo(
        client=ClientAPI(base_url=base_url, loop=get_loop()),
        secret=server.get("secret"),
        username=username,
        password=password,
        user_type=body.get("user_type", "bot"),
        device_name=body.get("device_name", "Maubot"),
        update_client=request.query.get("update_client", "").lower() in ("1", "true", "yes"),
    ), None


def generate_mac(secret: str, nonce: str, username: str, password: str, admin: bool = False,
                 user_type: str = None) -> str:
    mac = hmac.new(key=secret.encode("utf-8"), digestmod=hashlib.sha1)
    mac.update(nonce.encode("utf-8"))
    mac.update(b"\x00")
    mac.update(username.encode("utf-8"))
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
    req, err = await read_client_auth_request(request)
    if err is not None:
        return err
    if not req.secret:
        return resp.registration_secret_not_found
    path = SynapseAdminPath.v1.register
    res = await req.client.api.request(Method.GET, path)
    content = {
        "nonce": res["nonce"],
        "username": req.username,
        "password": req.password,
        "admin": False,
        "user_type": req.user_type,
    }
    content["mac"] = generate_mac(**content, secret=req.secret)
    try:
        raw_res = await req.client.api.request(Method.POST, path, content=content)
    except MatrixRequestError as e:
        return web.json_response({
            "errcode": e.errcode,
            "error": e.message,
            "http_status": e.http_status,
        }, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    login_res = LoginResponse.deserialize(raw_res)
    if req.update_client:
        return await _create_client(login_res.user_id, {
            "homeserver": str(req.client.api.base_url),
            "access_token": login_res.access_token,
            "device_id": login_res.device_id,
        })
    return web.json_response(login_res.serialize())


@routes.post("/client/auth/{server}/login")
async def login(request: web.Request) -> web.Response:
    req, err = await read_client_auth_request(request)
    if err is not None:
        return err
    device_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    try:
        res = await req.client.login(identifier=req.username, login_type=LoginType.PASSWORD,
                                     password=req.password, device_id=f"maubot_{device_id}",
                                     initial_device_display_name=req.device_name,
                                     store_access_token=False)
    except MatrixRequestError as e:
        return web.json_response({
            "errcode": e.errcode,
            "error": e.message,
        }, status=e.http_status)
    if req.update_client:
        return await _create_or_update_client(res.user_id, {
            "homeserver": str(req.client.api.base_url),
            "access_token": res.access_token,
            "device_id": res.device_id,
        }, is_login=True)
    return web.json_response(res.serialize())
