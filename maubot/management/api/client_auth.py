# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2019 Tulir Asokan
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
from mautrix.api import HTTPAPI, Path, Method
from mautrix.errors import MatrixRequestError

from .base import routes, get_config, get_loop
from .responses import resp


def registration_secrets() -> Dict[str, Dict[str, str]]:
    return get_config()["registration_secrets"]


def generate_mac(secret: str, nonce: str, user: str, password: str, admin: bool = False, user_type: str = None):
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


@routes.get("/client/auth/servers")
async def get_registerable_servers(_: web.Request) -> web.Response:
    return web.json_response({key: value["url"] for key, value in registration_secrets().items()})


AuthRequestInfo = NamedTuple("AuthRequestInfo", api=HTTPAPI, secret=str, username=str,
                             password=str, user_type=str)


async def read_client_auth_request(request: web.Request) -> Tuple[Optional[AuthRequestInfo],
                                                                  Optional[web.Response]]:
    server_name = request.match_info.get("server", None)
    server = registration_secrets().get(server_name, None)
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
        secret = server["secret"]
    except KeyError:
        return None, resp.invalid_server
    api = HTTPAPI(base_url, "", loop=get_loop())
    user_type = body.get("user_type", "bot")
    return AuthRequestInfo(api, secret, username, password, user_type), None


@routes.post("/client/auth/{server}/register")
async def register(request: web.Request) -> web.Response:
    info, err = await read_client_auth_request(request)
    if err is not None:
        return err
    api, secret, username, password, user_type = info
    res = await api.request(Method.GET, Path.admin.register)
    nonce = res["nonce"]
    mac = generate_mac(secret, nonce, username, password, user_type=user_type)
    try:
        return web.json_response(await api.request(Method.POST, Path.admin.register, content={
            "nonce": nonce,
            "username": username,
            "password": password,
            "admin": False,
            "mac": mac,
            # Older versions of synapse will ignore this field if it is None
            "user_type": user_type,
        }))
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
    api, _, username, password, _ = info
    device_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    try:
        return web.json_response(await api.request(Method.POST, Path.login, content={
            "type": "m.login.password",
            "identifier": {
                "type": "m.id.user",
                "user": username,
            },
            "password": password,
            "device_id": f"maubot_{device_id}",
        }))
    except MatrixRequestError as e:
        return web.json_response({
            "errcode": e.errcode,
            "error": e.message,
        }, status=e.http_status)
