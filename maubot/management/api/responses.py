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

ErrNoToken = web.json_response({
    "error": "Authorization token missing",
    "errcode": "auth_token_missing",
}, status=web.HTTPUnauthorized)

ErrInvalidToken = web.json_response({
    "error": "Invalid authorization token",
    "errcode": "auth_token_invalid",
}, status=web.HTTPUnauthorized)

ErrPluginNotFound = web.json_response({
    "error": "Plugin not found",
    "errcode": "plugin_not_found",
}, status=web.HTTPNotFound)

ErrPluginInUse = web.json_response({
    "error": "Plugin instances of this type still exist",
    "errcode": "plugin_in_use",
}, status=web.HTTPPreconditionFailed)


def ErrInputPluginInvalid(error) -> web.Response:
    return web.json_response({
        "error": str(error),
        "errcode": "plugin_invalid",
    }, status=web.HTTPBadRequest)


def ErrPluginReloadFailed(error) -> web.Response:
    return web.json_response({
        "error": str(error),
        "errcode": "plugin_invalid",
    }, status=web.HTTPInternalServerError)


ErrNotImplemented = web.json_response({
    "error": "Not implemented",
    "errcode": "not_implemented",
}, status=web.HTTPNotImplemented)

RespOK = web.json_response({
    "success": True,
}, status=web.HTTPOk)

RespDeleted = web.Response(status=web.HTTPNoContent)
