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
from http import HTTPStatus
from aiohttp import web

ErrBadAuth = web.json_response({
    "error": "Invalid username or password",
    "errcode": "invalid_auth",
}, status=HTTPStatus.UNAUTHORIZED)

ErrNoToken = web.json_response({
    "error": "Authorization token missing",
    "errcode": "auth_token_missing",
}, status=HTTPStatus.UNAUTHORIZED)

ErrInvalidToken = web.json_response({
    "error": "Invalid authorization token",
    "errcode": "auth_token_invalid",
}, status=HTTPStatus.UNAUTHORIZED)

ErrPluginNotFound = web.json_response({
    "error": "Plugin not found",
    "errcode": "plugin_not_found",
}, status=HTTPStatus.NOT_FOUND)

ErrClientNotFound = web.json_response({
    "error": "Client not found",
    "errcode": "client_not_found",
}, status=HTTPStatus.NOT_FOUND)

ErrPrimaryUserNotFound = web.json_response({
    "error": "Client for given primary user not found",
    "errcode": "primary_user_not_found",
}, status=HTTPStatus.NOT_FOUND)

ErrInstanceNotFound = web.json_response({
    "error": "Plugin instance not found",
    "errcode": "instance_not_found",
}, status=HTTPStatus.NOT_FOUND)

ErrPluginTypeNotFound = web.json_response({
    "error": "Given plugin type not found",
    "errcode": "plugin_type_not_found",
}, status=HTTPStatus.NOT_FOUND)

ErrPluginTypeRequired = web.json_response({
    "error": "Plugin type is required when creating plugin instances",
    "errcode": "plugin_type_required",
}, status=HTTPStatus.BAD_REQUEST)

ErrPrimaryUserRequired = web.json_response({
    "error": "Primary user is required when creating plugin instances",
    "errcode": "primary_user_required",
}, status=HTTPStatus.BAD_REQUEST)

ErrPathNotFound = web.json_response({
    "error": "Resource not found",
    "errcode": "resource_not_found",
}, status=HTTPStatus.NOT_FOUND)

ErrMethodNotAllowed = web.json_response({
    "error": "Method not allowed",
    "errcode": "method_not_allowed",
}, status=HTTPStatus.METHOD_NOT_ALLOWED)

ErrPluginInUse = web.json_response({
    "error": "Plugin instances of this type still exist",
    "errcode": "plugin_in_use",
}, status=HTTPStatus.PRECONDITION_FAILED)

ErrBodyNotJSON = web.json_response({
    "error": "Request body is not JSON",
    "errcode": "body_not_json",
}, status=HTTPStatus.BAD_REQUEST)


def plugin_import_error(error: str, stacktrace: str) -> web.Response:
    return web.json_response({
        "error": error,
        "stacktrace": stacktrace,
        "errcode": "plugin_invalid",
    }, status=HTTPStatus.BAD_REQUEST)


def plugin_reload_error(error: str, stacktrace: str) -> web.Response:
    return web.json_response({
        "error": error,
        "stacktrace": stacktrace,
        "errcode": "plugin_reload_fail",
    }, status=HTTPStatus.INTERNAL_SERVER_ERROR)


ErrUnsupportedPluginLoader = web.json_response({
    "error": "Existing plugin with same ID uses unsupported plugin loader",
    "errcode": "unsupported_plugin_loader",
}, status=HTTPStatus.BAD_REQUEST)

ErrNotImplemented = web.json_response({
    "error": "Not implemented",
    "errcode": "not_implemented",
}, status=HTTPStatus.NOT_IMPLEMENTED)

RespOK = web.json_response({
    "success": True,
}, status=HTTPStatus.OK)

RespDeleted = web.Response(status=HTTPStatus.NO_CONTENT)
