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

from typing import NamedTuple
from http import HTTPStatus
from json import JSONDecodeError
import asyncio
import hashlib
import hmac
import random
import string

from aiohttp import web
from yarl import URL

from mautrix.api import Method, Path, SynapseAdminPath
from mautrix.client import ClientAPI
from mautrix.errors import MatrixRequestError
from mautrix.types import LoginResponse, LoginType

from .base import get_config, routes
from .client import _create_client, _create_or_update_client
from .responses import resp


def known_homeservers() -> dict[str, dict[str, str]]:
    return get_config()["homeservers"]


@routes.get("/client/auth/servers")
async def get_known_servers(_: web.Request) -> web.Response:
    return web.json_response({key: value["url"] for key, value in known_homeservers().items()})


class AuthRequestInfo(NamedTuple):
    server_name: str
    client: ClientAPI
    secret: str
    username: str
    password: str
    user_type: str
    device_name: str
    update_client: bool
    sso: bool


truthy_strings = ("1", "true", "yes")


async def read_client_auth_request(
    request: web.Request,
) -> tuple[AuthRequestInfo | None, web.Response | None]:
    server_name = request.match_info.get("server", None)
    server = known_homeservers().get(server_name, None)
    if not server:
        return None, resp.server_not_found
    try:
        body = await request.json()
    except JSONDecodeError:
        return None, resp.body_not_json
    sso = request.query.get("sso", "").lower() in truthy_strings
    try:
        username = body["username"]
        password = body["password"]
    except KeyError:
        if not sso:
            return None, resp.username_or_password_missing
        username = password = None
    try:
        base_url = server["url"]
    except KeyError:
        return None, resp.invalid_server
    return (
        AuthRequestInfo(
            server_name=server_name,
            client=ClientAPI(base_url=base_url),
            secret=server.get("secret"),
            username=username,
            password=password,
            user_type=body.get("user_type", "bot"),
            device_name=body.get("device_name", "Maubot"),
            update_client=request.query.get("update_client", "").lower() in truthy_strings,
            sso=sso,
        ),
        None,
    )


def generate_mac(
    secret: str,
    nonce: str,
    username: str,
    password: str,
    admin: bool = False,
    user_type: str = None,
) -> str:
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
    if req.sso:
        return resp.registration_no_sso
    elif not req.secret:
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
        return web.json_response(
            {
                "errcode": e.errcode,
                "error": e.message,
                "http_status": e.http_status,
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    login_res = LoginResponse.deserialize(raw_res)
    if req.update_client:
        return await _create_client(
            login_res.user_id,
            {
                "homeserver": str(req.client.api.base_url),
                "access_token": login_res.access_token,
                "device_id": login_res.device_id,
            },
        )
    return web.json_response(login_res.serialize())


@routes.post("/client/auth/{server}/login")
async def login(request: web.Request) -> web.Response:
    req, err = await read_client_auth_request(request)
    if err is not None:
        return err
    if req.sso:
        return await _do_sso(req)
    else:
        return await _do_login(req)


async def _do_sso(req: AuthRequestInfo) -> web.Response:
    flows = await req.client.get_login_flows()
    if not flows.supports_type(LoginType.SSO):
        return resp.sso_not_supported
    waiter_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
    cfg = get_config()
    public_url = (
        URL(cfg["server.public_url"])
        / "_matrix/maubot/v1/client/auth_external_sso/complete"
        / waiter_id
    )
    sso_url = req.client.api.base_url.with_path(str(Path.v3.login.sso.redirect)).with_query(
        {"redirectUrl": str(public_url)}
    )
    sso_waiters[waiter_id] = req, asyncio.get_running_loop().create_future()
    return web.json_response({"sso_url": str(sso_url), "id": waiter_id})


async def _do_login(req: AuthRequestInfo, login_token: str | None = None) -> web.Response:
    device_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    device_id = f"maubot_{device_id}"
    try:
        if req.sso:
            res = await req.client.login(
                token=login_token,
                login_type=LoginType.TOKEN,
                device_id=device_id,
                store_access_token=False,
                initial_device_display_name=req.device_name,
            )
        else:
            res = await req.client.login(
                identifier=req.username,
                login_type=LoginType.PASSWORD,
                password=req.password,
                device_id=device_id,
                initial_device_display_name=req.device_name,
                store_access_token=False,
            )
    except MatrixRequestError as e:
        return web.json_response(
            {
                "errcode": e.errcode,
                "error": e.message,
            },
            status=e.http_status,
        )
    if req.update_client:
        return await _create_or_update_client(
            res.user_id,
            {
                "homeserver": str(req.client.api.base_url),
                "access_token": res.access_token,
                "device_id": res.device_id,
            },
            is_login=True,
        )
    return web.json_response(res.serialize())


sso_waiters: dict[str, tuple[AuthRequestInfo, asyncio.Future]] = {}


@routes.post("/client/auth/{server}/sso/{id}/wait")
async def wait_sso(request: web.Request) -> web.Response:
    waiter_id = request.match_info["id"]
    req, fut = sso_waiters[waiter_id]
    try:
        login_token = await fut
    finally:
        sso_waiters.pop(waiter_id, None)
    return await _do_login(req, login_token)


@routes.get("/client/auth_external_sso/complete/{id}")
async def complete_sso(request: web.Request) -> web.Response:
    try:
        _, fut = sso_waiters[request.match_info["id"]]
    except KeyError:
        return web.Response(status=404, text="Invalid session ID\n")
    if fut.cancelled():
        return web.Response(status=200, text="The login was cancelled from the Maubot client\n")
    elif fut.done():
        return web.Response(status=200, text="The login token was already received\n")
    try:
        fut.set_result(request.query["loginToken"])
    except KeyError:
        return web.Response(status=400, text="Missing loginToken query parameter\n")
    except asyncio.InvalidStateError:
        return web.Response(status=500, text="Invalid state\n")
    return web.Response(
        status=200,
        text="Login token received, please return to your Maubot client. "
        "This tab can be closed.\n",
    )
